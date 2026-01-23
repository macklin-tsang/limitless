package com.poker.agent.repository;

import com.poker.agent.model.GameResult;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * Repository for GameResult entities.
 * Provides CRUD operations and custom queries for game results.
 */
@Repository
public interface GameResultRepository extends JpaRepository<GameResult, Long> {

    /**
     * Find all game results for a specific user, ordered by timestamp descending.
     */
    List<GameResult> findByUser_IdOrderByTimestampDesc(Long userId);

    /**
     * Find all game results for a specific user and agent.
     */
    List<GameResult> findByUser_IdAndAgentName(Long userId, String agentName);

    /**
     * Count total games for a user.
     */
    long countByUser_Id(Long userId);

    /**
     * Count wins for a user.
     */
    long countByUser_IdAndResult(Long userId, String result);

    /**
     * Calculate total profit for a user.
     */
    @Query("SELECT COALESCE(SUM(g.profit), 0) FROM GameResult g WHERE g.user.id = :userId")
    java.math.BigDecimal sumProfitByUserId(@Param("userId") Long userId);

    /**
     * Calculate total hands played for a user.
     */
    @Query("SELECT COALESCE(SUM(g.handsPlayed), 0) FROM GameResult g WHERE g.user.id = :userId")
    Long sumHandsPlayedByUserId(@Param("userId") Long userId);

    /**
     * Calculate average profit per game for a user.
     */
    @Query("SELECT COALESCE(AVG(g.profit), 0) FROM GameResult g WHERE g.user.id = :userId")
    java.math.BigDecimal avgProfitByUserId(@Param("userId") Long userId);
}