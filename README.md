[**English**](README.md) | [Русский](README.ru.md)

# Toggl Quick Launcher

A simple, self-hosted, mobile-first web interface for quickly starting and stopping Toggl Track timers based on predefined projects.    

## Features

- **Dynamic Project Buttons:** Automatically creates buttons for each project in your Toggl workspace.
- **Daily Summary:** See the total time tracked for each project and for the entire day.
- **Live Timer:** The main timer ticks every second for a real-time feel.
- **Mobile First & Fully Responsive:** Looks and works great on any device, from phones (in portrait/landscape) to desktops.
- **PWA Ready:** Installable on your phone's home screen for a native, fullscreen app experience.
- **Self-Hosted & Secure:** Your Toggl API token stays on your server.
- **Dockerized:** Easy to deploy and manage with Docker and Docker Compose.

## Getting Started

### Prerequisites

- Docker and Docker Compose installed on your server.
- A Toggl Track account.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/toggl-webapp.git
    cd toggl-webapp
    ```

2.  **Create the environment file:**
    Copy the example file and edit it to add your API token.
    ```bash
    cp .env.example .env
    nano .env 
    ```
    Get your token from your Toggl Track profile settings page.

3.  **Run with Docker Compose:**
    ```bash
    docker-compose up -d
    ```
    The application will be running inside a Docker container.