#include <sys/resource.h>
#include <unistd.h>
#include <cstdio>
#include <cstdlib>

inline void set(int what, int value) {
    rlimit limit;
    limit.rlim_cur=limit.rlim_max=value;
    if(setrlimit(what,&limit)) {
        fprintf(stderr,"[JUDGER ERROR] cannot set %d limit",what);
        throw 1;
    }
}

int main(int argc, char *argv[]) {
    //argv[1]=mem_limit, argv[2]=time_limit
    if(argc!=3) {
        fprintf(stderr,"[JUDGER ERROR] bad argc");
        return 1;
    }

    set(RLIMIT_CPU,atoi(argv[2]));
    set(RLIMIT_NOFILE,0);
    set(RLIMIT_AS,atoi(argv[1]));
    set(RLIMIT_STACK,atoi(argv[1]));
    set(RLIMIT_NPROC,1);

    chroot("/home/judge");
    if(setuid(/*JUDGE_UID*/)) {
        fprintf(stderr,"[JUDGER ERROR] cannot setuid");
        return 1;
    }
    char *args[]={(char*)"/program",NULL};
    if(execv("/program",args)) {
        fprintf(stderr,"[JUDGER ERROR] cannot execute program");
        return 1;
    }
}