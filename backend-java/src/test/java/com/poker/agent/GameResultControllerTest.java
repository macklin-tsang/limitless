package com.poker.agent;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.poker.agent.dto.GameResultRequest;
import com.poker.agent.dto.SimulationRequest;
import com.poker.agent.model.GameResult;
import com.poker.agent.model.User;
import com.poker.agent.repository.GameResultRepository;
import com.poker.agent.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for GameResultController.
 * Uses H2 in-memory database for testing.
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
public class GameResultControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private GameResultRepository gameResultRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private ObjectMapper objectMapper;

    private User testUser;

    @BeforeEach
    void setUp() {
        gameResultRepository.deleteAll();
        userRepository.deleteAll();

        // Create a test user
        testUser = new User("testuser", "test@example.com");
        testUser = userRepository.save(testUser);
    }

    // ==================== POST /api/results ====================

    @Test
    void saveResult_ValidRequest_ReturnsCreatedResult() throws Exception {
        GameResultRequest request = new GameResultRequest();
        request.setUserId(testUser.getId());
        request.setAgentName("TAG Bot");
        request.setOpponentName("Random Bot");
        request.setResult("win");
        request.setProfit(new BigDecimal("150.50"));
        request.setHandsPlayed(100);

        mockMvc.perform(post("/api/results")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id", notNullValue()))
                .andExpect(jsonPath("$.agentName", is("TAG Bot")))
                .andExpect(jsonPath("$.opponentName", is("Random Bot")))
                .andExpect(jsonPath("$.result", is("win")))
                .andExpect(jsonPath("$.profit", is(150.50)))
                .andExpect(jsonPath("$.handsPlayed", is(100)))
                .andExpect(jsonPath("$.timestamp", notNullValue()));
    }

    @Test
    void saveResult_NonExistentUser_Returns404() throws Exception {
        GameResultRequest request = new GameResultRequest();
        request.setUserId(99999L);
        request.setAgentName("TAG Bot");
        request.setOpponentName("Random Bot");
        request.setResult("win");
        request.setProfit(new BigDecimal("100.00"));
        request.setHandsPlayed(50);

        mockMvc.perform(post("/api/results")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error", containsString("User not found")));
    }

    @Test
    void saveResult_MissingAgentName_ReturnsBadRequest() throws Exception {
        String invalidJson = "{\"userId\":" + testUser.getId() + ",\"opponentName\":\"Bot\",\"result\":\"win\",\"profit\":100,\"handsPlayed\":50}";

        mockMvc.perform(post("/api/results")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(invalidJson))
                .andExpect(status().isBadRequest());
    }

    @Test
    void saveResult_InvalidHandsPlayed_ReturnsBadRequest() throws Exception {
        GameResultRequest request = new GameResultRequest();
        request.setUserId(testUser.getId());
        request.setAgentName("TAG Bot");
        request.setOpponentName("Random Bot");
        request.setResult("win");
        request.setProfit(new BigDecimal("100.00"));
        request.setHandsPlayed(-5); // Invalid: negative

        mockMvc.perform(post("/api/results")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    // ==================== GET /api/results/user/{userId} ====================

    @Test
    void getResultsByUser_NoResults_ReturnsEmptyList() throws Exception {
        mockMvc.perform(get("/api/results/user/" + testUser.getId()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(0)));
    }

    @Test
    void getResultsByUser_WithResults_ReturnsResultList() throws Exception {
        // Create test game results
        GameResult result1 = new GameResult(testUser, "TAG Bot", "Random", "win", new BigDecimal("100"), 50);
        GameResult result2 = new GameResult(testUser, "LAG Bot", "Rock", "loss", new BigDecimal("-50"), 30);
        gameResultRepository.save(result1);
        gameResultRepository.save(result2);

        mockMvc.perform(get("/api/results/user/" + testUser.getId()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(2)));
    }

    @Test
    void getResultsByUser_NonExistentUser_Returns404() throws Exception {
        mockMvc.perform(get("/api/results/user/99999"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error", containsString("User not found")));
    }

    // ==================== GET /api/results/stats/{userId} ====================

    @Test
    void getStatsByUser_NoResults_ReturnsZeroStats() throws Exception {
        mockMvc.perform(get("/api/results/stats/" + testUser.getId()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.userId", is(testUser.getId().intValue())))
                .andExpect(jsonPath("$.totalGames", is(0)))
                .andExpect(jsonPath("$.wins", is(0)))
                .andExpect(jsonPath("$.losses", is(0)))
                .andExpect(jsonPath("$.winRate", is(0)))
                .andExpect(jsonPath("$.totalHandsPlayed", is(0)))
                .andExpect(jsonPath("$.totalProfit", is(0)));
    }

    @Test
    void getStatsByUser_WithResults_ReturnsAggregatedStats() throws Exception {
        // Create test game results: 2 wins, 1 loss
        gameResultRepository.save(new GameResult(testUser, "TAG", "Random", "win", new BigDecimal("100"), 50));
        gameResultRepository.save(new GameResult(testUser, "TAG", "Random", "win", new BigDecimal("80"), 40));
        gameResultRepository.save(new GameResult(testUser, "TAG", "LAG", "loss", new BigDecimal("-30"), 60));

        mockMvc.perform(get("/api/results/stats/" + testUser.getId()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.userId", is(testUser.getId().intValue())))
                .andExpect(jsonPath("$.totalGames", is(3)))
                .andExpect(jsonPath("$.wins", is(2)))
                .andExpect(jsonPath("$.losses", is(1)))
                .andExpect(jsonPath("$.winRate", closeTo(66.67, 0.01)))
                .andExpect(jsonPath("$.totalHandsPlayed", is(150)))
                .andExpect(jsonPath("$.totalProfit", is(150.0)));
    }

    @Test
    void getStatsByUser_NonExistentUser_Returns404() throws Exception {
        mockMvc.perform(get("/api/results/stats/99999"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error", containsString("User not found")));
    }

    // ==================== POST /api/simulate ====================

    @Test
    void runSimulation_ValidRequest_ReturnsSimulationResults() throws Exception {
        SimulationRequest request = new SimulationRequest();
        request.setUserId(testUser.getId());
        request.setAgentType("TAG");
        request.setOpponentType("Random");
        request.setNumGames(100);

        mockMvc.perform(post("/api/simulate")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.gameResultId", notNullValue()))
                .andExpect(jsonPath("$.agentName", is("TAG")))
                .andExpect(jsonPath("$.opponentName", is("Random")))
                .andExpect(jsonPath("$.gamesPlayed", is(100)))
                .andExpect(jsonPath("$.wins", notNullValue()))
                .andExpect(jsonPath("$.losses", notNullValue()))
                .andExpect(jsonPath("$.winRate", notNullValue()))
                .andExpect(jsonPath("$.totalProfit", notNullValue()))
                .andExpect(jsonPath("$.result", anyOf(is("win"), is("loss"))));
    }

    @Test
    void runSimulation_NonExistentUser_ReturnsBadRequest() throws Exception {
        SimulationRequest request = new SimulationRequest();
        request.setUserId(99999L);
        request.setAgentType("TAG");
        request.setOpponentType("Random");
        request.setNumGames(100);

        mockMvc.perform(post("/api/simulate")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error", containsString("User not found")));
    }

    @Test
    void runSimulation_InvalidNumGames_ReturnsBadRequest() throws Exception {
        SimulationRequest request = new SimulationRequest();
        request.setUserId(testUser.getId());
        request.setAgentType("TAG");
        request.setOpponentType("Random");
        request.setNumGames(0); // Invalid: must be at least 1

        mockMvc.perform(post("/api/simulate")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void runSimulation_TooManyGames_ReturnsBadRequest() throws Exception {
        SimulationRequest request = new SimulationRequest();
        request.setUserId(testUser.getId());
        request.setAgentType("TAG");
        request.setOpponentType("Random");
        request.setNumGames(100000); // Invalid: max is 10000

        mockMvc.perform(post("/api/simulate")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }

    @Test
    void runSimulation_MissingAgentType_ReturnsBadRequest() throws Exception {
        String invalidJson = "{\"userId\":" + testUser.getId() + ",\"opponentType\":\"Random\",\"numGames\":100}";

        mockMvc.perform(post("/api/simulate")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(invalidJson))
                .andExpect(status().isBadRequest());
    }

    @Test
    void runSimulation_SavesResultToDatabase() throws Exception {
        SimulationRequest request = new SimulationRequest();
        request.setUserId(testUser.getId());
        request.setAgentType("TAG");
        request.setOpponentType("Fish");
        request.setNumGames(50);

        mockMvc.perform(post("/api/simulate")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk());

        // Verify the result was saved
        mockMvc.perform(get("/api/results/user/" + testUser.getId()))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].agentName", is("TAG")))
                .andExpect(jsonPath("$[0].opponentName", is("Fish")));
    }
}
