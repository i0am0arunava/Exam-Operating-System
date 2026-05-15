/*
 * procman.h - Process Manager Header
 */

#ifndef PROCMAN_H
#define PROCMAN_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <signal.h>
#include <unistd.h>
#include <sys/types.h>

#define MAX_NAME    256
#define MAX_CMDLINE 1024

typedef struct {
    pid_t pid;
    pid_t ppid;
    char  name[MAX_NAME];
    char  state;
    int   num_threads;
    long  vmrss;    /* Resident Set Size in kB */
    long  vmsize;   /* Virtual memory size in kB */
    char  cmdline[MAX_CMDLINE];
} ProcessInfo;

/* Core functions */
void list_processes(void);
void search_process(void);
void kill_process_by_pid(void);
void show_process_info(void);
void top_cpu_processes(void);
void show_memory_usage(void);

/* Helpers */
int  read_process_info(pid_t pid, ProcessInfo *info);
int  is_pid_dir(const char *name);

#endif /* PROCMAN_H */
