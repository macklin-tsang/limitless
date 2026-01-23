package com.poker.agent.service;

import com.poker.agent.dto.GameResultRequest;
import com.poker.agent.dto.UserStatsResponse;
import com.poker.agent.model.GameResult;
import com.poker.agent.model.User;
import com.poker.agent.repository.GameResultRepository;
import com.poker.agent.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;
import java.util.Optional;

/**
 * Service for game result operations.
 */
@Service
public class GameResultService {

    private final GameResultRepository gameResultRepository;
    private final UserRepository userRepository;

    @Autowired
    public GameResultService(GameResultRepository gameResultRepository, UserRepository userRepository) {
        this.gameResultRepository = gameResultRepository;
        this.userRepository = userRepository;
    }

    /**
     * Save a new game result.
     */
    @Transactional
    public GameResult saveGameResult(GameResultRequest request) {
        User user = userRepository.findById(request.getUserId())
                .orElseThrow(() -> new IllegalArgumentException("User not found with id: " + request.getUserId()));

        GameResult gameResult = new GameResult(
                user,
                request.getAgentName(),
                request.getOpponentName(),
                request.getResult(),
                request.getProfit(),
                request.getHandsPlayed()
        );

        return gameResultRepository.save(gameResult);
    }

    /**
     * Get all game results for a user.
     */
    public List<GameResult> getResultsByUserId(Long userId) {
        if (!userRepository.existsById(userId)) {
            throw new IllegalArgumentException("User not found with id: " + userId);
        }
        return gameResultRepository.findByUser_IdOrderByTimestampDesc(userId);
    }

    /**
     * Get aggregated stats for a user.
     */
    public UserStatsResponse getStatsByUserId(Long userId) {
        if (!userRepository.existsById(userId)) {
            throw new IllegalArgumentException("User not found with id: " + userId);
        }

        UserStatsResponse stats = new UserStatsResponse();
        stats.setUserId(userId);

        long totalGames = gameResultRepository.countByUser_Id(userId);
        stats.setTotalGames(totalGames);

        long wins = gameResultRepository.countByUser_IdAndResult(userId, "win");
        stats.setWins(wins);
        stats.setLosses(totalGames - wins);

        if (totalGames > 0) {
            BigDecimal winRate = BigDecimal.valueOf(wins)
                    .divide(BigDecimal.valueOf(totalGames), 4, RoundingMode.HALF_UP)
                    .multiply(BigDecimal.valueOf(100));
            stats.setWinRate(winRate);
        } else {
            stats.setWinRate(BigDecimal.ZERO);
        }

        Long totalHands = gameResultRepository.sumHandsPlayedByUserId(userId);
        stats.setTotalHandsPlayed(totalHands != null ? totalHands : 0L);

        BigDecimal totalProfit = gameResultRepository.sumProfitByUserId(userId);
        stats.setTotalProfit(totalProfit != null ? totalProfit : BigDecimal.ZERO);

        BigDecimal avgProfit = gameResultRepository.avgProfitByUserId(userId);
        stats.setAvgProfitPerGame(avgProfit != null ? avgProfit.setScale(2, RoundingMode.HALF_UP) : BigDecimal.ZERO);

        if (totalHands != null && totalHands > 0) {
            BigDecimal profitPerHand = totalProfit.divide(BigDecimal.valueOf(totalHands), 4, RoundingMode.HALF_UP);
            stats.setProfitPerHand(profitPerHand);
        } else {
            stats.setProfitPerHand(BigDecimal.ZERO);
        }

        return stats;
    }

    /**
     * Get a game result by ID.
     */
    public Optional<GameResult> getResultById(Long id) {
        return gameResultRepository.findById(id);
    }
}
