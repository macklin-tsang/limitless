package com.poker.agent.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;

/**
 * DTO for creating a game result.
 */
public class GameResultRequest {

    @NotNull(message = "User ID is required")
    private Long userId;

    @NotBlank(message = "Agent name is required")
    @Size(max = 50, message = "Agent name must be at most 50 characters")
    private String agentName;

    @NotBlank(message = "Opponent name is required")
    @Size(max = 50, message = "Opponent name must be at most 50 characters")
    private String opponentName;

    @NotBlank(message = "Result is required")
    @Size(max = 10, message = "Result must be at most 10 characters")
    private String result;

    @NotNull(message = "Profit is required")
    private BigDecimal profit;

    @NotNull(message = "Hands played is required")
    @Positive(message = "Hands played must be positive")
    private Integer handsPlayed;

    public GameResultRequest() {
    }

    // Getters and Setters

    public Long getUserId() {
        return userId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public String getAgentName() {
        return agentName;
    }

    public void setAgentName(String agentName) {
        this.agentName = agentName;
    }

    public String getOpponentName() {
        return opponentName;
    }

    public void setOpponentName(String opponentName) {
        this.opponentName = opponentName;
    }

    public String getResult() {
        return result;
    }

    public void setResult(String result) {
        this.result = result;
    }

    public BigDecimal getProfit() {
        return profit;
    }

    public void setProfit(BigDecimal profit) {
        this.profit = profit;
    }

    public Integer getHandsPlayed() {
        return handsPlayed;
    }

    public void setHandsPlayed(Integer handsPlayed) {
        this.handsPlayed = handsPlayed;
    }

    @Override
    public String toString() {
        return "GameResultRequest{" +
                "userId=" + userId +
                ", agentName='" + agentName + '\'' +
                ", opponentName='" + opponentName + '\'' +
                ", result='" + result + '\'' +
                ", profit=" + profit +
                ", handsPlayed=" + handsPlayed +
                '}';
    }
}
