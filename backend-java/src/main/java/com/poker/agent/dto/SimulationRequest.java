package com.poker.agent.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

/**
 * DTO for simulation request parameters.
 */
public class SimulationRequest {

    @NotNull(message = "User ID is required")
    private Long userId;

    @NotBlank(message = "Agent type is required")
    private String agentType;

    @NotBlank(message = "Opponent type is required")
    private String opponentType;

    @NotNull(message = "Number of games is required")
    @Min(value = 1, message = "Number of games must be at least 1")
    @Max(value = 10000, message = "Number of games must be at most 10000")
    private Integer numGames;

    @Positive(message = "Small blind must be positive")
    private Integer smallBlind = 1;

    @Positive(message = "Big blind must be positive")
    private Integer bigBlind = 2;

    public SimulationRequest() {
    }

    public SimulationRequest(Long userId, String agentType, String opponentType, Integer numGames) {
        this.userId = userId;
        this.agentType = agentType;
        this.opponentType = opponentType;
        this.numGames = numGames;
    }

    // Getters and Setters

    public Long getUserId() {
        return userId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public String getAgentType() {
        return agentType;
    }

    public void setAgentType(String agentType) {
        this.agentType = agentType;
    }

    public String getOpponentType() {
        return opponentType;
    }

    public void setOpponentType(String opponentType) {
        this.opponentType = opponentType;
    }

    public Integer getNumGames() {
        return numGames;
    }

    public void setNumGames(Integer numGames) {
        this.numGames = numGames;
    }

    public Integer getSmallBlind() {
        return smallBlind;
    }

    public void setSmallBlind(Integer smallBlind) {
        this.smallBlind = smallBlind;
    }

    public Integer getBigBlind() {
        return bigBlind;
    }

    public void setBigBlind(Integer bigBlind) {
        this.bigBlind = bigBlind;
    }

    @Override
    public String toString() {
        return "SimulationRequest{" +
                "userId=" + userId +
                ", agentType='" + agentType + '\'' +
                ", opponentType='" + opponentType + '\'' +
                ", numGames=" + numGames +
                ", smallBlind=" + smallBlind +
                ", bigBlind=" + bigBlind +
                '}';
    }
}
