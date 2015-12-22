#include <sys/resource.h>
#include <wait.h>
#include <unistd.h>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <fstream>

inline void lim(int what, int value) {
    rlimit limit;
    limit.rlim_cur=limit.rlim_max=value;
    if(setrlimit(what,&limit)) {
        fprintf(stderr,"[JUDGER ERROR] cannot set %d limit",what);
        exit(1);
    }
}

int main(int argc, char *argv[]) {
    int rtn;
    rusage usage;

    //argv[1]=mem_limit in bytes, argv[2]=time_limit
    if(argc!=3) {
        fprintf(stderr,"[JUDGER ERROR] bad argc");
        return 1;
    }

    FILE *f=fopen("/root/result.txt","w+");
    if(f==NULL) {
        fprintf(stderr,"[JUDGER ERROR] cannot open result file");
        return 1;
    }
    fprintf(f,"JUDGER\n");

    lim(RLIMIT_CPU,atoi(argv[2]));
    lim(RLIMIT_NOFILE,1);
    lim(RLIMIT_AS,atoi(argv[1]));
    lim(RLIMIT_STACK,atoi(argv[1]));
    lim(RLIMIT_NPROC,2);

    char *args[]={(char*)"/program",NULL};

    pid_t forked=fork();
    if(forked<0) {
        fprintf(stderr,"[JUDGER ERROR] cannot fork");
        return 1;
    }
    else if(forked==0) { //sub
        if(chroot("/home/judge")) {
            fprintf(stderr,"[JUDGER ERROR] cannot chroot");
            return 1;
        }
        if(setuid(/*JUDGE_UID*/)) {
            fprintf(stderr,"[JUDGER ERROR] cannot setuid");
            return 1;
        }
        if(execv("/program",args)) {
            fprintf(stderr,"[JUDGER ERROR] cannot execute program");
            return 1;
        }
    }
    else { //main
        getrusage(RUSAGE_CHILDREN,&usage);
        timeval start_time=usage.ru_utime;

        wait(&rtn);
        getrusage(RUSAGE_CHILDREN,&usage);
        timeval stop_time=usage.ru_utime;

        fprintf(f,"%ld\n",1000000*stop_time.tv_sec+stop_time.tv_usec - 1000000*start_time.tv_sec-start_time.tv_usec); //sec
        if(WIFEXITED(rtn))
            return WEXITSTATUS(rtn);
        else {
            fprintf(stderr,"[JUDGER ERROR] wait status = %d",rtn);
            return 1;
        }
    }
}