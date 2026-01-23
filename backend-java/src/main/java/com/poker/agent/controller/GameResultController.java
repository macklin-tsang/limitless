package com.poker.agent.controller;

import com.poker.agent.dto.GameResultRequest;
import com.poker.agent.dto.SimulationRequest;
import com.poker.agent.dto.SimulationResponse;
import com.poker.agent.dto.UserStatsResponse;
import com.poker.agent.model.GameResult;
import com.poker.agent.service.GameResultService;
import com.poker.agent.service.SimulationService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * REST Controller for game results and simulations.
 */
@RestController
@RequestMapping("/api")
public class GameResultController {

    private final GameResultService gameResultService;
    private final SimulationService simulationService;

    @Autowired
    public GameResultController(GameResultService gameResultService, SimulationService simulationService) {
        this.gameResultService = gameResultService;
        this.simulationService = simulationService;
    }

    /**
     * Save a game result.
     *
     * POST /api/results
     */
    @PostMapping("/results")
    public ResponseEntity<?> saveResult(@Valid @RequestBody GameResultRequest request) {
        try {
            GameResult result = gameResultService.saveGameResult(request);
            return ResponseEntity.status(HttpStatus.CREATED).body(result);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(createErrorResponse(e.getMessage()));
        }
    }

    /**
     * Get all game results for a user.
     *
     * GET /api/results/user/{userId}
     */
    @GetMapping("/results/user/{userId}")
    public ResponseEntity<?> getResultsByUser(@PathVariable Long userId) {
        try {
            List<GameResult> results = gameResultService.getResultsByUserId(userId);
            return ResponseEntity.ok(results);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(createErrorResponse(e.getMessage()));
        }
    }

    /**
     * Get aggregated stats for a user.
     *
     * GET /api/results/stats/{userId}
     */
    @GetMapping("/results/stats/{userId}")
    public ResponseEntity<?> getStatsByUser(@PathVariable Long userId) {
        try {
            UserStatsResponse stats = gameResultService.getStatsByUserId(userId);
            return ResponseEntity.ok(stats);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(createErrorResponse(e.getMessage()));
        }
    }

    /**
     * Run a simulation.
     *
     * POST /api/simulate
     */
    @PostMapping("/simulate")
    public ResponseEntity<?> runSimulation(@Valid @RequestBody SimulationRequest request) {
        try {
            SimulationResponse response = simulationService.runSimulation(request);
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(createErrorResponse(e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(createErrorResponse("Simulation failed: " + e.getMessage()));
        }
    }

    /**
     * Create a standardized error response.
     */
    private Map<String, String> createErrorResponse(String message) {
        Map<String, String> error = new HashMap<>();
        error.put("error", message);
        return error;
    }
}
