package com.poker.agent.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.*;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.Size;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * Entity representing a game result between an agent and opponent.
 */
@Entity
@Table(name = "game_results")
public class GameResult {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    @JsonIgnore
    private User user;

    @NotBlank(message = "Agent name is required")
    @Size(max = 50, message = "Agent name must be at most 50 characters")
    @Column(name = "agent_name", nullable = false, length = 50)
    private String agentName;

    @NotBlank(message = "Opponent name is required")
    @Size(max = 50, message = "Opponent name must be at most 50 characters")
    @Column(name = "opponent_name", nullable = false, length = 50)
    private String opponentName;

    @NotBlank(message = "Result is required")
    @Size(max = 10, message = "Result must be at most 10 characters")
    @Column(nullable = false, length = 10)
    private String result;

    @NotNull(message = "Profit is required")
    @Column(nullable = false, precision = 10, scale = 2)
    private BigDecimal profit;

    @NotNull(message = "Hands played is required")
    @Positive(message = "Hands played must be positive")
    @Column(name = "hands_played", nullable = false)
    private Integer handsPlayed;

    @Column(name = "timestamp", nullable = false, updatable = false)
    private LocalDateTime timestamp;

    public GameResult() {
    }

    public GameResult(User user, String agentName, String opponentName,
                      String result, BigDecimal profit, Integer handsPlayed) {
        this.user = user;
        this.agentName = agentName;
        this.opponentName = opponentName;
        this.result = result;
        this.profit = profit;
        this.handsPlayed = handsPlayed;
    }

    @PrePersist
    protected void onCreate() {
        this.timestamp = LocalDateTime.now();
    }

    // Getters and Setters

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public User getUser() {
        return user;
    }

    public void setUser(User user) {
        this.user = user;
    }

    @JsonProperty("userId")
    public Long getUserId() {
        return user != null ? user.getId() : null;
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

    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(LocalDateTime timestamp) {
        this.timestamp = timestamp;
    }

    @Override
    public String toString() {
        return "GameResult{" +
                "id=" + id +
                ", userId=" + (user != null ? user.getId() : null) +
                ", agentName='" + agentName + '\'' +
                ", opponentName='" + opponentName + '\'' +
                ", result='" + result + '\'' +
                ", profit=" + profit +
                ", handsPlayed=" + handsPlayed +
                ", timestamp=" + timestamp +
                '}';
    }
}