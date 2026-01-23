package com.poker.agent.dto;

import java.math.BigDecimal;

/**
 * DTO for user aggregated statistics.
 */
public class UserStatsResponse {

    private Long userId;
    private Long totalGames;
    private Long wins;
    private Long losses;
    private BigDecimal winRate;
    private Long totalHandsPlayed;
    private BigDecimal totalProfit;
    private BigDecimal avgProfitPerGame;
    private BigDecimal profitPerHand;

    public UserStatsResponse() {
    }

    // Getters and Setters

    public Long getUserId() {
        return userId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public Long getTotalGames() {
        return totalGames;
    }

    public void setTotalGames(Long totalGames) {
        this.totalGames = totalGames;
    }

    public Long getWins() {
        return wins;
    }

    public void setWins(Long wins) {
        this.wins = wins;
    }

    public Long getLosses() {
        return losses;
    }

    public void setLosses(Long losses) {
        this.losses = losses;
    }

    public BigDecimal getWinRate() {
        return winRate;
    }

    public void setWinRate(BigDecimal winRate) {
        this.winRate = winRate;
    }

    public Long getTotalHandsPlayed() {
        return totalHandsPlayed;
    }

    public void setTotalHandsPlayed(Long totalHandsPlayed) {
        this.totalHandsPlayed = totalHandsPlayed;
    }

    public BigDecimal getTotalProfit() {
        return totalProfit;
    }

    public void setTotalProfit(BigDecimal totalProfit) {
        this.totalProfit = totalProfit;
    }

    public BigDecimal getAvgProfitPerGame() {
        return avgProfitPerGame;
    }

    public void setAvgProfitPerGame(BigDecimal avgProfitPerGame) {
        this.avgProfitPerGame = avgProfitPerGame;
    }

    public BigDecimal getProfitPerHand() {
        return profitPerHand;
    }

    public void setProfitPerHand(BigDecimal profitPerHand) {
        this.profitPerHand = profitPerHand;
    }

    @Override
    public String toString() {
        return "UserStatsResponse{" +
                "userId=" + userId +
                ", totalGames=" + totalGames +
                ", wins=" + wins +
                ", losses=" + losses +
                ", winRate=" + winRate +
                ", totalHandsPlayed=" + totalHandsPlayed +
                ", totalProfit=" + totalProfit +
                ", avgProfitPerGame=" + avgProfitPerGame +
                ", profitPerHand=" + profitPerHand +
                '}';
    }
}
