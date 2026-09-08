# Mini CI/CD Platform

A lightweight Python-based CI/CD platform that automates project testing, build execution, artifact storage, and pipeline reporting.

## Features

* Automatic project type detection
* Test and build pipeline stages
* Queue-based job execution
* Pipeline failure handling
* Build artifact storage
* Run ID generation
* JSON pipeline reports
* Python and Node.js support
* Demo project generation
* CLI support

## Tech Stack

**Python | CLI | subprocess | deque | JSON | File System**

## DSA Used

**Queue | deque | Dictionary | List | Set-based filtering**

## Usage

Run in the current project:

```bash
python mini_cicd_platform_fixed.py
```

Run the built-in demo:

```bash
python mini_cicd_platform_fixed.py --demo
```

Run against another project:

```bash
python mini_cicd_platform_fixed.py "C:\Path\To\Project"
```

Generate a JSON report:

```bash
python mini_cicd_platform_fixed.py --demo --json cicd_report.json
```

## Pipeline

```text
Project
   ↓
Detection
   ↓
Job Queue
   ↓
Tests
   ↓
Build
   ↓
Artifact Storage
   ↓
Pipeline Report
```

## Purpose

Designed to demonstrate CI/CD concepts, automation, job queues, build pipelines, artifact management, and Python-based developer tooling.


