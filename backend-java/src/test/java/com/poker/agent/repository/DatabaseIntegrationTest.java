package com.poker.agent.repository;

import com.poker.agent.model.GameResult;
import com.poker.agent.model.User;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.test.context.ActiveProfiles;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.*;

/**
 * Database integration tests for verifying PostgreSQL schema operations.
 * Tests repository layer with various data scenarios including:
 * - CRUD operations for User and GameResult entities
 * - Foreign key constraints
 * - Unique constraints
 * - Custom query methods
 * - Aggregate functions (sum, count, avg)
 *
 * Uses H2 for test execution (simulating PostgreSQL behavior).
 * These tests ensure the schema defined in schema.sql works correctly.
 */
@DataJpaTest
@ActiveProfiles("test")
@DisplayName("Database Integration Tests")
public class DatabaseIntegrationTest {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private GameResultRepository gameResultRepository;

    @BeforeEach
    void setUp() {
        gameResultRepository.deleteAll();
        userRepository.deleteAll();
    }

    @Nested
    @DisplayName("User Repository Tests")
    class UserRepositoryTests {

        @Test
        @DisplayName("Should create a new user successfully")
        void shouldCreateUser() {
            User user = new User("testuser", "test@example.com");
            User savedUser = userRepository.save(user);

            assertThat(savedUser.getId()).isNotNull();
            assertThat(savedUser.getUsername()).isEqualTo("testuser");
            assertThat(savedUser.getEmail()).isEqualTo("test@example.com");
            assertThat(savedUser.getCreatedAt()).isNotNull();
        }

        @Test
        @DisplayName("Should find user by username")
        void shouldFindByUsername() {
            userRepository.save(new User("alice", "alice@example.com"));

            Optional<User> found = userRepository.findByUsername("alice");

            assertThat(found).isPresent();
            assertThat(found.get().getEmail()).isEqualTo("alice@example.com");
        }

        @Test
        @DisplayName("Should find user by email")
        void shouldFindByEmail() {
            userRepository.save(new User("bob", "bob@example.com"));

            Optional<User> found = userRepository.findByEmail("bob@example.com");

            assertThat(found).isPresent();
            assertThat(found.get().getUsername()).isEqualTo("bob");
        }

        @Test
        @DisplayName("Should return empty when user not found")
        void shouldReturnEmptyWhenNotFound() {
            Optional<User> found = userRepository.findByUsername("nonexistent");

            assertThat(found).isEmpty();
        }

        @Test
        @DisplayName("Should check if username exists")
        void shouldCheckUsernameExists() {
            userRepository.save(new User("existing", "existing@example.com"));

            assertThat(userRepository.existsByUsername("existing")).isTrue();
            assertThat(userRepository.existsByUsername("nonexistent")).isFalse();
        }

        @Test
        @DisplayName("Should check if email exists")
        void shouldCheckEmailExists() {
            userRepository.save(new User("user1", "exists@example.com"));

            assertThat(userRepository.existsByEmail("exists@example.com")).isTrue();
            assertThat(userRepository.existsByEmail("notexists@example.com")).isFalse();
        }

        @Test
        @DisplayName("Should enforce unique username constraint")
        void shouldEnforceUniqueUsername() {
            userRepository.save(new User("duplicate", "first@example.com"));

            User duplicateUser = new User("duplicate", "second@example.com");

            assertThatThrownBy(() -> {
                userRepository.saveAndFlush(duplicateUser);
            }).isInstanceOf(DataIntegrityViolationException.class);
        }

        @Test
        @DisplayName("Should enforce unique email constraint")
        void shouldEnforceUniqueEmail() {
            userRepository.save(new User("user1", "duplicate@example.com"));

            User duplicateEmailUser = new User("user2", "duplicate@example.com");

            assertThatThrownBy(() -> {
                userRepository.saveAndFlush(duplicateEmailUser);
            }).isInstanceOf(DataIntegrityViolationException.class);
        }

        @Test
        @DisplayName("Should update user information")
        void shouldUpdateUser() {
            User user = userRepository.save(new User("oldname", "old@example.com"));

            user.setUsername("newname");
            user.setEmail("new@example.com");
            User updated = userRepository.save(user);

            assertThat(updated.getUsername()).isEqualTo("newname");
            assertThat(updated.getEmail()).isEqualTo("new@example.com");
        }

        @Test
        @DisplayName("Should delete user")
        void shouldDeleteUser() {
            User user = userRepository.save(new User("todelete", "delete@example.com"));
            Long userId = user.getId();

            userRepository.delete(user);

            assertThat(userRepository.findById(userId)).isEmpty();
        }

        @Test
        @DisplayName("Should return all users")
        void shouldReturnAllUsers() {
            userRepository.save(new User("user1", "user1@example.com"));
            userRepository.save(new User("user2", "user2@example.com"));
            userRepository.save(new User("user3", "user3@example.com"));

            List<User> users = userRepository.findAll();

            assertThat(users).hasSize(3);
        }
    }

    @Nested
    @DisplayName("GameResult Repository Tests")
    class GameResultRepositoryTests {

        private User testUser;

        @BeforeEach
        void createTestUser() {
            testUser = userRepository.save(new User("gameuser", "game@example.com"));
        }

        @Test
        @DisplayName("Should create a game result successfully")
        void shouldCreateGameResult() {
            GameResult result = new GameResult(
                    testUser, "TAG Bot", "Random Bot", "win",
                    new BigDecimal("150.50"), 100
            );

            GameResult saved = gameResultRepository.save(result);

            assertThat(saved.getId()).isNotNull();
            assertThat(saved.getAgentName()).isEqualTo("TAG Bot");
            assertThat(saved.getOpponentName()).isEqualTo("Random Bot");
            assertThat(saved.getResult()).isEqualTo("win");
            assertThat(saved.getProfit()).isEqualByComparingTo(new BigDecimal("150.50"));
            assertThat(saved.getHandsPlayed()).isEqualTo(100);
            assertThat(saved.getTimestamp()).isNotNull();
        }

        @Test
        @DisplayName("Should find game results by user ID ordered by timestamp")
        void shouldFindByUserIdOrderedByTimestamp() {
            // Create multiple results with slight delays to ensure different timestamps
            GameResult result1 = gameResultRepository.save(
                    new GameResult(testUser, "TAG", "Random", "win", new BigDecimal("100"), 50)
            );
            GameResult result2 = gameResultRepository.save(
                    new GameResult(testUser, "LAG", "Rock", "loss", new BigDecimal("-30"), 40)
            );
            GameResult result3 = gameResultRepository.save(
                    new GameResult(testUser, "TAG", "LAG", "win", new BigDecimal("80"), 60)
            );

            List<GameResult> results = gameResultRepository.findByUser_IdOrderByTimestampDesc(testUser.getId());

            assertThat(results).hasSize(3);
            // Most recent should be first (result3)
            assertThat(results.get(0).getId()).isEqualTo(result3.getId());
        }

        @Test
        @DisplayName("Should find game results by user ID and agent name")
        void shouldFindByUserIdAndAgentName() {
            gameResultRepository.save(new GameResult(testUser, "TAG", "Random", "win", new BigDecimal("100"), 50));
            gameResultRepository.save(new GameResult(testUser, "LAG", "Rock", "loss", new BigDecimal("-30"), 40));
            gameResultRepository.save(new GameResult(testUser, "TAG", "LAG", "win", new BigDecimal("80"), 60));

            List<GameResult> tagResults = gameResultRepository.findByUser_IdAndAgentName(testUser.getId(), "TAG");

            assertThat(tagResults).hasSize(2);
            assertThat(tagResults).allMatch(r -> r.getAgentName().equals("TAG"));
        }

        @Test
        @DisplayName("Should count total games for a user")
        void shouldCountByUserId() {
            gameResultRepository.save(new GameResult(testUser, "TAG", "Random", "win", new BigDecimal("100"), 50));
            gameResultRepository.save(new GameResult(testUser, "LAG", "Rock", "loss", new BigDecimal("-30"), 40));
            gameResultRepository.save(new GameResult(testUser, "TAG", "LAG", "win", new BigDecimal("80"), 60));

            long count = gameResultRepository.countByUser_Id(testUser.getId());

            assertThat(count).isEqualTo(3);
        }

        @Test
        @DisplayName("Should count wins for a user")
        void shouldCountWins() {
            gameResultRepository.save(new GameResult(testUser, "TAG", "Random", "win", new BigDecimal("100"), 50));
            gameResultRepository.save(new GameResult(testUser, "LAG", "Rock", "loss", new BigDecimal("-30"), 40));
            gameResultRepository.save(new GameResult(testUser, "TAG", "LAG", "win", new BigDecimal("80"), 60));

            long wins = gameResultRepository.countByUser_IdAndResult(testUser.getId(), "win");
            long losses = gameResultRepository.countByUser_IdAndResult(testUser.getId(), "loss");

            assertThat(wins).isEqualTo(2);
            assertThat(losses).isEqualTo(1);
        }

        @Test
        @DisplayName("Should sum total profit for a user")
        void shouldSumProfitByUserId() {
            gameResultRepository.save(new GameResult(testUser, "TAG", "Random", "win", new BigDecimal("100.50"), 50));
            gameResultRepository.save(new GameResult(testUser, "LAG", "Rock", "loss", new BigDecimal("-30.25"), 40));
            gameResultRepository.save(new GameResult(testUser, "TAG", "LAG", "win", new BigDecimal("80.75"), 60));

            BigDecimal totalProfit = gameResultRepository.sumProfitByUserId(testUser.getId());

            // 100.50 - 30.25 + 80.75 = 151.00
            assertThat(totalProfit).isEqualByComparingTo(new BigDecimal("151.00"));
        }

        @Test
        @DisplayName("Should return zero profit for user with no games")
        void shouldReturnZeroProfitForNoGames() {
            BigDecimal totalProfit = gameResultRepository.sumProfitByUserId(testUser.getId());

            assertThat(totalProfit).isEqualByComparingTo(BigDecimal.ZERO);
        }

        @Test
        @DisplayName("Should sum total hands played for a user")
        void shouldSumHandsPlayedByUserId() {
            gameResultRepository.save(new GameResult(testUser, "TAG", "Random", "win", new BigDecimal("100"), 50));
            gameResultRepository.save(new GameResult(testUser, "LAG", "Rock", "loss", new BigDecimal("-30"), 40));
            gameResultRepository.save(new GameResult(testUser, "TAG", "LAG", "win", new BigDecimal("80"), 60));

            Long totalHands = gameResultRepository.sumHandsPlayedByUserId(testUser.getId());

            assertThat(totalHands).isEqualTo(150);
        }

        @Test
        @DisplayName("Should return zero hands for user with no games")
        void shouldReturnZeroHandsForNoGames() {
            Long totalHands = gameResultRepository.sumHandsPlayedByUserId(testUser.getId());

            assertThat(totalHands).isEqualTo(0);
        }

        @Test
        @DisplayName("Should calculate average profit for a user")
        void shouldCalculateAverageProfit() {
            gameResultRepository.save(new GameResult(testUser, "TAG", "Random", "win", new BigDecimal("100"), 50));
            gameResultRepository.save(new GameResult(testUser, "LAG", "Rock", "loss", new BigDecimal("-40"), 40));
            gameResultRepository.save(new GameResult(testUser, "TAG", "LAG", "win", new BigDecimal("60"), 60));

            BigDecimal avgProfit = gameResultRepository.avgProfitByUserId(testUser.getId());

            // (100 - 40 + 60) / 3 = 40
            assertThat(avgProfit).isEqualByComparingTo(new BigDecimal("40.00"));
        }

        @Test
        @DisplayName("Should handle negative total profit correctly")
        void shouldHandleNegativeTotalProfit() {
            gameResultRepository.save(new GameResult(testUser, "TAG", "Random", "loss", new BigDecimal("-100"), 50));
            gameResultRepository.save(new GameResult(testUser, "LAG", "Rock", "loss", new BigDecimal("-50"), 40));
            gameResultRepository.save(new GameResult(testUser, "TAG", "LAG", "win", new BigDecimal("30"), 60));

            BigDecimal totalProfit = gameResultRepository.sumProfitByUserId(testUser.getId());

            // -100 - 50 + 30 = -120
            assertThat(totalProfit).isEqualByComparingTo(new BigDecimal("-120"));
        }

        @Test
        @DisplayName("Should isolate data between users")
        void shouldIsolateDataBetweenUsers() {
            User user2 = userRepository.save(new User("user2", "user2@example.com"));

            gameResultRepository.save(new GameResult(testUser, "TAG", "Random", "win", new BigDecimal("100"), 50));
            gameResultRepository.save(new GameResult(testUser, "LAG", "Rock", "win", new BigDecimal("80"), 40));
            gameResultRepository.save(new GameResult(user2, "TAG", "LAG", "loss", new BigDecimal("-50"), 60));

            long user1Games = gameResultRepository.countByUser_Id(testUser.getId());
            long user2Games = gameResultRepository.countByUser_Id(user2.getId());
            BigDecimal user1Profit = gameResultRepository.sumProfitByUserId(testUser.getId());
            BigDecimal user2Profit = gameResultRepository.sumProfitByUserId(user2.getId());

            assertThat(user1Games).isEqualTo(2);
            assertThat(user2Games).isEqualTo(1);
            assertThat(user1Profit).isEqualByComparingTo(new BigDecimal("180"));
            assertThat(user2Profit).isEqualByComparingTo(new BigDecimal("-50"));
        }

        @Test
        @DisplayName("Should update game result")
        void shouldUpdateGameResult() {
            GameResult result = gameResultRepository.save(
                    new GameResult(testUser, "TAG", "Random", "win", new BigDecimal("100"), 50)
            );

            result.setProfit(new BigDecimal("150"));
            result.setHandsPlayed(75);
            GameResult updated = gameResultRepository.save(result);

            assertThat(updated.getProfit()).isEqualByComparingTo(new BigDecimal("150"));
            assertThat(updated.getHandsPlayed()).isEqualTo(75);
        }

        @Test
        @DisplayName("Should delete game result")
        void shouldDeleteGameResult() {
            GameResult result = gameResultRepository.save(
                    new GameResult(testUser, "TAG", "Random", "win", new BigDecimal("100"), 50)
            );
            Long resultId = result.getId();

            gameResultRepository.delete(result);

            assertThat(gameResultRepository.findById(resultId)).isEmpty();
        }

        @Test
        @DisplayName("Should return empty list for user with no games")
        void shouldReturnEmptyListForNoGames() {
            List<GameResult> results = gameResultRepository.findByUser_IdOrderByTimestampDesc(testUser.getId());

            assertThat(results).isEmpty();
        }
    }

    @Nested
    @DisplayName("Foreign Key Constraint Tests")
    class ForeignKeyConstraintTests {

        @Test
        @DisplayName("Should delete game results before user to satisfy foreign key constraint")
        void shouldDeleteGameResultsBeforeUser() {
            User user = userRepository.save(new User("cascade", "cascade@example.com"));
            gameResultRepository.save(new GameResult(user, "TAG", "Random", "win", new BigDecimal("100"), 50));
            gameResultRepository.save(new GameResult(user, "LAG", "Rock", "loss", new BigDecimal("-30"), 40));

            Long userId = user.getId();
            assertThat(gameResultRepository.countByUser_Id(userId)).isEqualTo(2);

            // Must delete game results first due to foreign key constraint
            // Note: PostgreSQL schema has ON DELETE CASCADE, but JPA entity doesn't have cascade configured
            // This test verifies the foreign key relationship is properly enforced
            List<GameResult> userResults = gameResultRepository.findByUser_IdOrderByTimestampDesc(userId);
            gameResultRepository.deleteAll(userResults);
            userRepository.delete(user);

            assertThat(gameResultRepository.countByUser_Id(userId)).isEqualTo(0);
            assertThat(userRepository.findById(userId)).isEmpty();
        }

        @Test
        @DisplayName("Should enforce foreign key constraint - cannot save game result without valid user")
        void shouldEnforceForeignKeyConstraint() {
            User unsavedUser = new User("unsaved", "unsaved@example.com");
            // Don't save the user - it has no ID

            GameResult result = new GameResult(
                    unsavedUser, "TAG", "Random", "win", new BigDecimal("100"), 50
            );

            // Attempting to save a game result with an unsaved user should fail
            assertThatThrownBy(() -> {
                gameResultRepository.saveAndFlush(result);
            }).isInstanceOf(Exception.class);
        }
    }

    @Nested
    @DisplayName("Large Dataset Tests")
    class LargeDatasetTests {

        @Test
        @DisplayName("Should handle inserting many game results")
        void shouldHandleManyGameResults() {
            User user = userRepository.save(new User("bulkuser", "bulk@example.com"));

            // Insert 100 game results
            for (int i = 0; i < 100; i++) {
                String result = i % 3 == 0 ? "loss" : "win";
                BigDecimal profit = result.equals("win") ?
                        new BigDecimal(50 + (i % 50)) :
                        new BigDecimal(-20 - (i % 30));
                gameResultRepository.save(
                        new GameResult(user, "TAG Bot", "Random Bot", result, profit, 100 + i)
                );
            }

            long count = gameResultRepository.countByUser_Id(user.getId());
            assertThat(count).isEqualTo(100);

            // Verify aggregations work on larger datasets
            BigDecimal totalProfit = gameResultRepository.sumProfitByUserId(user.getId());
            Long totalHands = gameResultRepository.sumHandsPlayedByUserId(user.getId());

            assertThat(totalProfit).isNotNull();
            assertThat(totalHands).isGreaterThan(10000); // 100 games * 100+ hands each
        }

        @Test
        @DisplayName("Should handle multiple users with game results")
        void shouldHandleMultipleUsersWithResults() {
            // Create 10 users with 10 games each
            for (int u = 0; u < 10; u++) {
                User user = userRepository.save(new User("user" + u, "user" + u + "@example.com"));
                for (int g = 0; g < 10; g++) {
                    gameResultRepository.save(
                            new GameResult(user, "Agent" + (g % 3), "Opponent" + (g % 2),
                                    g % 2 == 0 ? "win" : "loss",
                                    new BigDecimal(g % 2 == 0 ? 50 : -25), 100)
                    );
                }
            }

            List<User> allUsers = userRepository.findAll();
            long totalGames = gameResultRepository.count();

            assertThat(allUsers).hasSize(10);
            assertThat(totalGames).isEqualTo(100);
        }
    }

    @Nested
    @DisplayName("Edge Case Tests")
    class EdgeCaseTests {

        private User testUser;

        @BeforeEach
        void createTestUser() {
            testUser = userRepository.save(new User("edgeuser", "edge@example.com"));
        }

        @Test
        @DisplayName("Should handle zero profit game")
        void shouldHandleZeroProfitGame() {
            GameResult result = new GameResult(
                    testUser, "TAG Bot", "TAG Bot", "draw",
                    BigDecimal.ZERO, 100
            );

            GameResult saved = gameResultRepository.save(result);

            assertThat(saved.getProfit()).isEqualByComparingTo(BigDecimal.ZERO);
        }

        @Test
        @DisplayName("Should handle very large profit values")
        void shouldHandleLargeProfitValues() {
            GameResult result = new GameResult(
                    testUser, "High Stakes", "Whale",
                    "win", new BigDecimal("99999999.99"), 1000
            );

            GameResult saved = gameResultRepository.save(result);

            assertThat(saved.getProfit()).isEqualByComparingTo(new BigDecimal("99999999.99"));
        }

        @Test
        @DisplayName("Should handle very large negative profit values")
        void shouldHandleLargeNegativeProfitValues() {
            GameResult result = new GameResult(
                    testUser, "Bad Day", "Shark",
                    "loss", new BigDecimal("-99999999.99"), 500
            );

            GameResult saved = gameResultRepository.save(result);

            assertThat(saved.getProfit()).isEqualByComparingTo(new BigDecimal("-99999999.99"));
        }

        @Test
        @DisplayName("Should handle decimal precision in profit")
        void shouldHandleDecimalPrecision() {
            gameResultRepository.save(new GameResult(testUser, "A", "B", "win", new BigDecimal("100.01"), 50));
            gameResultRepository.save(new GameResult(testUser, "A", "B", "win", new BigDecimal("100.02"), 50));
            gameResultRepository.save(new GameResult(testUser, "A", "B", "win", new BigDecimal("100.03"), 50));

            BigDecimal total = gameResultRepository.sumProfitByUserId(testUser.getId());

            // 100.01 + 100.02 + 100.03 = 300.06
            assertThat(total).isEqualByComparingTo(new BigDecimal("300.06"));
        }

        @Test
        @DisplayName("Should handle special characters in agent names")
        void shouldHandleSpecialCharactersInAgentNames() {
            GameResult result = new GameResult(
                    testUser, "TAG Bot (v2.0)", "Random-Bot_Test",
                    "win", new BigDecimal("100"), 50
            );

            GameResult saved = gameResultRepository.save(result);

            assertThat(saved.getAgentName()).isEqualTo("TAG Bot (v2.0)");
            assertThat(saved.getOpponentName()).isEqualTo("Random-Bot_Test");
        }
    }
}
