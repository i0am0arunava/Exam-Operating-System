/*
 * procman.c - Simple Process Manager for Linux
 * Lists, kills, and monitors system processes
 */

#include "procman.h"

int main(int argc, char *argv[]) {
    int choice;

    printf("\033[1;36m");
    printf("╔══════════════════════════════╗\n");
    printf("║      PROCESS MANAGER v1.0    ║\n");
    printf("╚══════════════════════════════╝\n");
    printf("\033[0m");

    while (1) {
        printf("\n\033[1;33m[MENU]\033[0m\n");
        printf("  1. List all processes\n");
        printf("  2. Search process by name\n");
        printf("  3. Kill process by PID\n");
        printf("  4. Show process info\n");
        printf("  5. Show top CPU processes\n");
        printf("  6. Show memory usage\n");
        printf("  0. Exit\n");
        printf("\nChoice: ");

        if (scanf("%d", &choice) != 1) break;

        switch (choice) {
            case 1: list_processes(); break;
            case 2: search_process(); break;
            case 3: kill_process_by_pid(); break;
            case 4: show_process_info(); break;
            case 5: top_cpu_processes(); break;
            case 6: show_memory_usage(); break;
            case 0:
                printf("Goodbye.\n");
                return 0;
            default:
                printf("Invalid option.\n");
        }
    }
    return 0;
}

/* List all running processes by reading /proc */
void list_processes(void) {
    DIR *proc_dir = opendir("/proc");
    struct dirent *entry;
    int count = 0;

    if (!proc_dir) {
        perror("opendir /proc");
        return;
    }

    printf("\n\033[1;32m%-8s %-20s %-10s %s\033[0m\n", "PID", "NAME", "STATE", "CMDLINE");
    printf("%-8s %-20s %-10s %s\n", "---", "----", "-----", "-------");

    while ((entry = readdir(proc_dir)) != NULL) {
        if (!is_pid_dir(entry->d_name)) continue;

        pid_t pid = (pid_t)atoi(entry->d_name);
        ProcessInfo info;
        if (read_process_info(pid, &info) == 0) {
            printf("%-8d %-20s %-10c %s\n",
                   info.pid, info.name, info.state, info.cmdline);
            count++;
        }
    }

    closedir(proc_dir);
    printf("\nTotal processes: %d\n", count);
}

/* Search for a process by name */
void search_process(void) {
    char name[MAX_NAME];
    printf("Enter process name: ");
    scanf("%255s", name);

    DIR *proc_dir = opendir("/proc");
    struct dirent *entry;
    int found = 0;

    if (!proc_dir) { perror("opendir"); return; }

    printf("\n\033[1;32m%-8s %-20s %-10s\033[0m\n", "PID", "NAME", "STATE");

    while ((entry = readdir(proc_dir)) != NULL) {
        if (!is_pid_dir(entry->d_name)) continue;

        pid_t pid = (pid_t)atoi(entry->d_name);
        ProcessInfo info;
        if (read_process_info(pid, &info) == 0) {
            if (strstr(info.name, name) != NULL) {
                printf("%-8d %-20s %-10c\n", info.pid, info.name, info.state);
                found++;
            }
        }
    }

    closedir(proc_dir);
    if (!found) printf("No process found with name: %s\n", name);
    else printf("\nFound: %d match(es)\n", found);
}

/* Kill a process by PID */
void kill_process_by_pid(void) {
    pid_t pid;
    int sig;

    printf("Enter PID to kill: ");
    scanf("%d", &pid);
    printf("Signal (9=SIGKILL, 15=SIGTERM): ");
    scanf("%d", &sig);

    if (kill(pid, sig) == 0) {
        printf("\033[1;32mSignal %d sent to PID %d\033[0m\n", sig, pid);
    } else {
        perror("kill");
    }
}

/* Show detailed info for a specific PID */
void show_process_info(void) {
    pid_t pid;
    printf("Enter PID: ");
    scanf("%d", &pid);

    ProcessInfo info;
    if (read_process_info(pid, &info) != 0) {
        printf("Could not read info for PID %d\n", pid);
        return;
    }

    printf("\n\033[1;36m=== Process Info: PID %d ===\033[0m\n", pid);
    printf("  Name     : %s\n", info.name);
    printf("  State    : %c\n", info.state);
    printf("  PID      : %d\n", info.pid);
    printf("  PPID     : %d\n", info.ppid);
    printf("  Threads  : %d\n", info.num_threads);
    printf("  VmRSS    : %ld kB\n", info.vmrss);
    printf("  VmSize   : %ld kB\n", info.vmsize);
    printf("  Cmdline  : %s\n", info.cmdline);
}

/* Show top 10 CPU-consuming processes using /proc/stat */
void top_cpu_processes(void) {
    printf("\n\033[1;33mTop CPU processes (via ps):\033[0m\n");
    system("ps -eo pid,comm,%cpu,%mem --sort=-%cpu | head -11");
}

/* Show memory usage summary */
void show_memory_usage(void) {
    FILE *f = fopen("/proc/meminfo", "r");
    if (!f) { perror("fopen /proc/meminfo"); return; }

    char line[256];
    long mem_total = 0, mem_free = 0, mem_available = 0, buffers = 0, cached = 0;

    while (fgets(line, sizeof(line), f)) {
        if (sscanf(line, "MemTotal: %ld kB", &mem_total) == 1) continue;
        if (sscanf(line, "MemFree: %ld kB", &mem_free) == 1) continue;
        if (sscanf(line, "MemAvailable: %ld kB", &mem_available) == 1) continue;
        if (sscanf(line, "Buffers: %ld kB", &buffers) == 1) continue;
        if (sscanf(line, "Cached: %ld kB", &cached) == 1) continue;
    }
    fclose(f);

    long used = mem_total - mem_free - buffers - cached;
    int pct = (mem_total > 0) ? (int)((used * 100) / mem_total) : 0;

    printf("\n\033[1;36m=== Memory Usage ===\033[0m\n");
    printf("  Total    : %7ld MB\n", mem_total / 1024);
    printf("  Used     : %7ld MB  (%d%%)\n", used / 1024, pct);
    printf("  Free     : %7ld MB\n", mem_free / 1024);
    printf("  Available: %7ld MB\n", mem_available / 1024);
    printf("  Buffers  : %7ld MB\n", buffers / 1024);
    printf("  Cached   : %7ld MB\n", cached / 1024);

    /* ASCII bar */
    printf("\n  [");
    int bars = pct / 5;
    for (int i = 0; i < 20; i++)
        printf("%s", i < bars ? "\033[1;31m#\033[0m" : "-");
    printf("] %d%%\n", pct);
}

/* Read process info from /proc/<pid>/status and /proc/<pid>/cmdline */
int read_process_info(pid_t pid, ProcessInfo *info) {
    char path[64];
    char line[256];

    memset(info, 0, sizeof(*info));
    info->pid = pid;

    /* Read /proc/<pid>/status */
    snprintf(path, sizeof(path), "/proc/%d/status", pid);
    FILE *f = fopen(path, "r");
    if (!f) return -1;

    while (fgets(line, sizeof(line), f)) {
        sscanf(line, "Name:\t%255s", info->name);
        sscanf(line, "State:\t%c", &info->state);
        sscanf(line, "PPid:\t%d", &info->ppid);
        sscanf(line, "Threads:\t%d", &info->num_threads);
        sscanf(line, "VmRSS:\t%ld", &info->vmrss);
        sscanf(line, "VmSize:\t%ld", &info->vmsize);
    }
    fclose(f);

    /* Read /proc/<pid>/cmdline */
    snprintf(path, sizeof(path), "/proc/%d/cmdline", pid);
    f = fopen(path, "r");
    if (f) {
        int c, i = 0;
        while ((c = fgetc(f)) != EOF && i < MAX_CMDLINE - 1) {
            info->cmdline[i++] = (c == '\0') ? ' ' : (char)c;
        }
        info->cmdline[i] = '\0';
        fclose(f);
    }

    return 0;
}

/* Returns 1 if the directory name is a numeric PID */
int is_pid_dir(const char *name) {
    if (!name || *name == '\0') return 0;
    for (const char *p = name; *p; p++)
        if (*p < '0' || *p > '9') return 0;
    return 1;
}
