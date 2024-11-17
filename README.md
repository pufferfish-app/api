<p align="center">
  <img src="https://github.com/user-attachments/assets/b336b7d7-df3c-401d-bd56-eaac242d2836" width="512">
  <h1 align="center">Pufferfish Infrastructure</h1>
</p>

<p align="center"><b>Backend IaC that powers the Pufferfish app</b></p>

## What is in this repo?

This repository contains a FastAPI API that forms the backend of the Pufferfish application. It provides an interface for user creation and management, a setup flow for connecting the application to a user's financial data via SimpleFIN Bridge, tools to analyze that data to detect possible fraud, as well as functionality for AI summarization of gathered insights.

## How is this used?

The application in this repository is distributed as a Docker container based on [this Dockerfile](https://github.com/pufferfish-app/api/blob/main/Dockerfile). The Docker container is built and deployed to GHCR automatically using GitHub Actions, and then pulled in and deployed by a DigitalOcean App Platform app.
