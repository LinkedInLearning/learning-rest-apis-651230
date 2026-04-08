54# Learning REST APIs

This is the repository for the LinkedIn Learning course `Learning REST APIs`. The full course is available from [LinkedIn Learning][lil-course-url].

![course-name-alt-text][lil-thumbnail-url]

## Course Description

Learn the basics of REST APIs. In this course, discover what REST APIs are, why they matter, and how putting them to use can help you build faster, more efficient applications. Review how HTTP and REST APIs relate, explore the six constraints of REST, and learn about HTTP status messages. Learn how to get started with consuming REST APIs to incorporate them into data-driven applications.

## Instructions

This repository serves as a practice environment for interacting with a database server through a REST API. When you open the repository in GitHub Codespaces, it spins up and populates a private database server with dummy content you can use to practice creating, retrieving, updating, modifying, and deleteting data through a typical REST API.

> [!NOTE]
> The Codespace takes quite a while to boot up for the first time. You'll know when it's ready when you get a message similar to this in Terminal:

```bash
INFO:     Started server process [5183]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

> [!CAUTION]
> This repo contains a live `.env` file and `.gitignore` does not ignore this file. In normal circumstances this would be a security issue and __strongly__ discouraged. This repo is an exceptional exception because the database server the `.env` file provides access to only exists in the virtual Codespaces environment. If you are not comfortable with having a live `.env` file in your fork, add `.env` to `.gitignore` and use the `.env.devcontainer` file as your template.
__DO NOT PUSH THIS REPO AS-IS TO PRODUCTION!__


## Branches

This repository has only one branch: `main`.

## Installing

The setup of this respository is automated in GitHub Codespaces. The only configuration you need to make on your own is making the REST API available to VS Code. This requires changing the REST API port from Private to Public:

1. Select the Ports tab in the bottom panel
2. Find the row for the `8000` port
3. In the "Visibility" column, right-click on "Private"
4. In the pop-up menu, select "Port Visibility -> Public"

## Expanding the database

The database is auto-populated with the contents of `init_db.py`. If you want to start with a larger dataset, you can modify and expand the contents of this file to your liking in your own fork and start a new Codespace.

## REST API documentation

Use of the REST API is covered in the course. You'll also find comprehensive documentation of the REST API in `DOCUMENTATION.md`.

[0]: # "Replace these placeholder URLs with actual course URLs"
[lil-course-url]: https://www.linkedin.com/learning/learning-rest-apis
[lil-thumbnail-url]: https://cdn.lynda.com/course/651230/651230-1564006888040-16x9.jpg
