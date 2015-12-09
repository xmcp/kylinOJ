#include <sys/resource.h>
#include <unistd.h>
#include <cstdio>
#include <cstdlib>

inline void lim(int what, int value) {
    rlimit limit;
    limit.rlim_cur=limit.rlim_max=value;
    if(setrlimit(what,&limit)) {
        fprintf(stderr,"[JUDGER ERROR] cannot set %d limit",what);
        exit(1);
    }
}

int main(int argc, char *argv[]) {
    //argv[1]=mem_limit, argv[2]=time_limit
    if(argc!=3) {
        fprintf(stderr,"[JUDGER ERROR] bad argc");
        return 1;
    }

    lim(RLIMIT_CPU,atoi(argv[2]));
    lim(RLIMIT_NOFILE,0);
    lim(RLIMIT_AS,atoi(argv[1]));
    lim(RLIMIT_STACK,atoi(argv[1]));
    lim(RLIMIT_NPROC,1);

    if(chroot("/home/judge")) {
        fprintf(stderr,"[JUDGER ERROR] cannot chroot");
        return 1;
    }
    if(setuid(/*JUDGE_UID*/)) {
        fprintf(stderr,"[JUDGER ERROR] cannot setuid");
        return 1;
    }
    char *args[]={(char*)"/program",NULL};
    if(execv("/program",args)) {
        fprintf(stderr,"[JUDGER ERROR] cannot execute program");
        return 1;
    }
    return 1; //should never happen
}