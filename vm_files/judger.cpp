#include <sys/resource.h>
#include <unistd.h>
#include <cstdio>
#include <errno.h>
#include <cstdlib>

inline void set(int what, int value) {
    rlimit limit;
    limit.rlim_cur=limit.rlim_max=value;
    if(setrlimit(what,&limit)!=0) {
        printf("[FAILED] errno = %d",errno);
        throw -10087;
    }
}

int main(int argc, char *argv[]) {
    //argv[1]=mem_limit, argv[2]=time_limit
    if(argc!=3) return -10086;

    set(RLIMIT_CPU,atoi(argv[2]));
    set(RLIMIT_NOFILE,0);
    set(RLIMIT_AS,atoi(argv[1]));
    set(RLIMIT_STACK,atoi(argv[1]));
    set(RLIMIT_NPROC,1);

    char *args[]={(char*)"/program",NULL};
    chroot("/home/judge");
    if(execv("/program",args))
        return -10088;
}