#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <libgen.h>
#include <limits.h>
#include <mach-o/dyld.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#ifndef PYTHON_HOME
#error "compile with -DPYTHON_HOME=..."
#endif
#ifndef PYTHON_SITE
#error "compile with -DPYTHON_SITE=..."
#endif

static int parent_dir(char *path) {
    char *slash = strrchr(path, '/');
    if (slash == NULL || slash == path) {
        return -1;
    }
    *slash = '\0';
    return 0;
}

int main(int argc, char **argv) {
    (void)argc;
    (void)argv;

    char exe[PATH_MAX];
    uint32_t size = sizeof(exe);
    if (_NSGetExecutablePath(exe, &size) != 0) {
        fprintf(stderr, "VozBar: executable path too long\n");
        return 1;
    }

    char resolved[PATH_MAX];
    if (realpath(exe, resolved) == NULL) {
        perror("VozBar: realpath");
        return 1;
    }

    /* VozBar.app/Contents/MacOS/VozBar → repo root is ../../../.. */
    char cursor[PATH_MAX];
    strncpy(cursor, resolved, sizeof(cursor) - 1);
    cursor[sizeof(cursor) - 1] = '\0';
    if (parent_dir(cursor) != 0 || parent_dir(cursor) != 0
        || parent_dir(cursor) != 0 || parent_dir(cursor) != 0) {
        fprintf(stderr, "VozBar: could not climb to repo root\n");
        return 1;
    }

    char repo[PATH_MAX];
    if (realpath(cursor, repo) == NULL) {
        perror("VozBar: repo realpath");
        return 1;
    }

    char app_py[PATH_MAX];
    snprintf(app_py, sizeof(app_py), "%s/app.py", repo);
    const char *site = PYTHON_SITE;

    if (chdir(repo) != 0) {
        perror("VozBar: chdir");
        return 1;
    }

    char pythonpath[PATH_MAX * 2];
    snprintf(pythonpath, sizeof(pythonpath), "%s:%s", repo, PYTHON_SITE);
    setenv("VOZBAR_BUNDLE", "1", 1);
    setenv("PYTHONPATH", pythonpath, 1);

    wchar_t *program = Py_DecodeLocale(resolved, NULL);
    wchar_t *home = Py_DecodeLocale(PYTHON_HOME, NULL);
    if (program == NULL || home == NULL) {
        fprintf(stderr, "VozBar: Py_DecodeLocale failed\n");
        return 1;
    }

    Py_SetProgramName(program);
    Py_SetPythonHome(home);
    Py_Initialize();

    FILE *fp = fopen(app_py, "r");
    if (fp == NULL) {
        fprintf(stderr, "VozBar: cannot open %s\n", app_py);
        return 1;
    }
    int run_rc = PyRun_SimpleFileEx(fp, app_py, 1);
    if (Py_FinalizeEx() < 0) {
        return 120;
    }
    PyMem_RawFree(program);
    PyMem_RawFree(home);
    return run_rc == 0 ? 0 : 1;
}
