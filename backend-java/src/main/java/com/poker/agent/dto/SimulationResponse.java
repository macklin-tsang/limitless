package com.poker.agent.dto;

import java.math.BigDecimal;

/**
 * DTO for simulation response/results.
 */
public class SimulationResponse {

    private Long gameResultId;
    private String agentName;
    private String opponentName;
    private Integer gamesPlayed;
    private Integer wins;
    private Integer losses;
    private BigDecimal winRate;
    private BigDecimal totalProfit;
    private BigDecimal profitPerHand;
    private String result;

    public SimulationResponse() {
    }

    // Getters and Setters

    public Long getGameResultId() {
        return gameResultId;
    }

    public void setGameResultId(Long gameResultId) {
        this.gameResultId = gameResultId;
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

    public Integer getGamesPlayed() {
        return gamesPlayed;
    }

    public void setGamesPlayed(Integer gamesPlayed) {
        this.gamesPlayed = gamesPlayed;
    }

    public Integer getWins() {
        return wins;
    }

    public void setWins(Integer wins) {
        this.wins = wins;
    }

    public Integer getLosses() {
        return losses;
    }

    public void setLosses(Integer losses) {
        this.losses = losses;
    }

    public BigDecimal getWinRate() {
        return winRate;
    }

    public void setWinRate(BigDecimal winRate) {
        this.winRate = winRate;
    }

    public BigDecimal getTotalProfit() {
        return totalProfit;
    }

    public void setTotalProfit(BigDecimal totalProfit) {
        this.totalProfit = totalProfit;
    }

    public BigDecimal getProfitPerHand() {
        return profitPerHand;
    }

    public void setProfitPerHand(BigDecimal profitPerHand) {
        this.profitPerHand = profitPerHand;
    }

    public String getResult() {
        return result;
    }

    public void setResult(String result) {
        this.result = result;
    }

    @Override
    public String toString() {
        return "SimulationResponse{" +
                "gameResultId=" + gameResultId +
                ", agentName='" + agentName + '\'' +
                ", opponentName='" + opponentName + '\'' +
                ", gamesPlayed=" + gamesPlayed +
                ", wins=" + wins +
                ", losses=" + losses +
                ", winRate=" + winRate +
                ", totalProfit=" + totalProfit +
                ", profitPerHand=" + profitPerHand +
                ", result='" + result + '\'' +
                '}';
    }
}
