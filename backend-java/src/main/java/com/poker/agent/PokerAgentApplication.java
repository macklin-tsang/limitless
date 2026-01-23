package com.poker.agent;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Main application entry point for the Poker Agent API.
 *
 * This Spring Boot application provides REST APIs for:
 * - User management
 * - Game results storage and retrieval
 * - Simulation triggers and statistics
 */
@SpringBootApplication
public class PokerAgentApplication {

    public static void main(String[] args) {
        SpringApplication.run(PokerAgentApplication.class, args);
    }
}
