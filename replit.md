# Overview

This is a Telegram bot built with Python that provides URL shortening and file handling services. The bot allows users to shorten URLs and upload/store files up to 4GB, with automatic backup to Telegram's storage infrastructure. It features admin controls, user management, and comprehensive statistics tracking.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Framework
- **Pyrogram**: Asynchronous Telegram client library for handling bot interactions
- **Python asyncio**: Event loop architecture for concurrent operations
- **SQLite with aiosqlite**: Lightweight, async database for user data and URL mappings

## Bot Structure
- **Modular Handler System**: Separate modules for admin, user, file, and URL operations
- **Configuration Management**: Environment-based config system for credentials and settings
- **Session Management**: Persistent bot sessions stored in dedicated session directory

## Database Design
- **Users Table**: Stores user profiles, join dates, ban status, and usage statistics
- **Short URLs Table**: Maps shortened codes to original URLs with click tracking
- **File Storage Table**: Tracks uploaded files with metadata and Telegram message IDs
- **Settings Table**: Bot configuration and admin preferences

## File Handling Architecture
- **Chunked Upload System**: Large files processed in 1MB chunks for memory efficiency
- **Multi-format Support**: Automatic file type detection and categorization
- **Telegram Storage Backend**: Files stored as Telegram messages in a dedicated storage channel
- **Size Limits**: 4GB maximum file size with validation and progress tracking

## URL Shortening System
- **Custom Domain Support**: Configurable branded short URLs
- **Collision-free Generation**: Automatic retry mechanism for unique short codes
- **Click Analytics**: Comprehensive tracking of URL access patterns
- **URL Validation**: Regex-based URL format verification

## Security & Access Control
- **Admin Role System**: Owner and admin roles with different permission levels
- **User Management**: Ban/unban functionality and user activity monitoring
- **Input Validation**: Sanitization of URLs and file inputs
- **Rate Limiting**: Built-in Pyrogram flood protection

## Logging & Monitoring
- **Comprehensive Logging**: File and console logging with different severity levels
- **Error Handling**: Graceful degradation with user-friendly error messages
- **Uptime Tracking**: System status monitoring and performance metrics

# External Dependencies

## Core Libraries
- **Pyrogram**: Telegram MTProto API client for bot functionality
- **aiosqlite**: Asynchronous SQLite database operations
- **aiofiles**: Async file I/O operations for large file handling

## Telegram Integration
- **Telegram Bot API**: Primary interface for bot operations
- **Storage Channel**: Dedicated Telegram channel for file backup storage
- **Session Storage**: Pyrogram session management for persistent connections

## Infrastructure Requirements
- **SQLite Database**: Local database file for persistent data storage
- **File System**: Local directories for temporary file processing
- **Environment Variables**: Configuration management for API keys and settings

## Optional Services
- **Custom Domain**: User-configurable domain for branded short URLs
- **External API Key**: Optional integration for enhanced URL shortening features