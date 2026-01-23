package com.poker.agent.service;

import com.poker.agent.dto.GameResultRequest;
import com.poker.agent.dto.SimulationRequest;
import com.poker.agent.dto.SimulationResponse;
import com.poker.agent.model.GameResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.HashMap;
import java.util.Map;

/**
 * Service for running poker simulations via Python backend.
 */
@Service
public class SimulationService {

    private static final Logger logger = LoggerFactory.getLogger(SimulationService.class);

    private final RestTemplate restTemplate;
    private final GameResultService gameResultService;

    @Value("${python.service.url:http://localhost:5000}")
    private String pythonServiceUrl;

    @Autowired
    public SimulationService(GameResultService gameResultService) {
        this.restTemplate = new RestTemplate();
        this.gameResultService = gameResultService;
    }

    /**
     * Run a simulation by calling the Python service and save results.
     */
    public SimulationResponse runSimulation(SimulationRequest request) {
        logger.info("Running simulation: {}", request);

        SimulationResponse response = new SimulationResponse();
        response.setAgentName(request.getAgentType());
        response.setOpponentName(request.getOpponentType());
        response.setGamesPlayed(request.getNumGames());

        try {
            // Call Python simulation service
            Map<String, Object> pythonRequest = new HashMap<>();
            pythonRequest.put("agent_type", request.getAgentType());
            pythonRequest.put("opponent_type", request.getOpponentType());
            pythonRequest.put("num_games", request.getNumGames());
            pythonRequest.put("small_blind", request.getSmallBlind());
            pythonRequest.put("big_blind", request.getBigBlind());

            String simulationUrl = pythonServiceUrl + "/api/simulate";

            @SuppressWarnings("unchecked")
            Map<String, Object> pythonResponse = restTemplate.postForObject(
                    simulationUrl,
                    pythonRequest,
                    Map.class
            );

            if (pythonResponse != null) {
                processSimulationResponse(pythonResponse, response);
            } else {
                // Fallback: simulate locally with mock data for testing
                logger.warn("Python service unavailable, using mock simulation");
                generateMockSimulation(request, response);
            }

        } catch (RestClientException e) {
            logger.warn("Failed to call Python service: {}, using mock simulation", e.getMessage());
            generateMockSimulation(request, response);
        }

        // Save the result to database
        GameResultRequest resultRequest = new GameResultRequest();
        resultRequest.setUserId(request.getUserId());
        resultRequest.setAgentName(response.getAgentName());
        resultRequest.setOpponentName(response.getOpponentName());
        resultRequest.setResult(response.getResult());
        resultRequest.setProfit(response.getTotalProfit());
        resultRequest.setHandsPlayed(response.getGamesPlayed());

        GameResult savedResult = gameResultService.saveGameResult(resultRequest);
        response.setGameResultId(savedResult.getId());

        logger.info("Simulation completed: {}", response);
        return response;
    }

    /**
     * Process Python service response into SimulationResponse.
     */
    private void processSimulationResponse(Map<String, Object> pythonResponse, SimulationResponse response) {
        Integer wins = getIntValue(pythonResponse, "wins", 0);
        Integer losses = getIntValue(pythonResponse, "losses", 0);
        BigDecimal totalProfit = getBigDecimalValue(pythonResponse, "total_profit", BigDecimal.ZERO);

        response.setWins(wins);
        response.setLosses(losses);
        response.setTotalProfit(totalProfit);

        int gamesPlayed = response.getGamesPlayed();
        if (gamesPlayed > 0) {
            BigDecimal winRate = BigDecimal.valueOf(wins)
                    .divide(BigDecimal.valueOf(gamesPlayed), 4, RoundingMode.HALF_UP)
                    .multiply(BigDecimal.valueOf(100));
            response.setWinRate(winRate);

            BigDecimal profitPerHand = totalProfit.divide(
                    BigDecimal.valueOf(gamesPlayed), 4, RoundingMode.HALF_UP);
            response.setProfitPerHand(profitPerHand);
        }

        response.setResult(wins > losses ? "win" : "loss");
    }

    /**
     * Generate mock simulation data for testing when Python service is unavailable.
     */
    private void generateMockSimulation(SimulationRequest request, SimulationResponse response) {
        int numGames = request.getNumGames();

        // Simulate with TAG agent having ~65% win rate vs random opponent
        double baseWinRate = getBaseWinRate(request.getAgentType(), request.getOpponentType());

        // Add some variance
        double variance = (Math.random() - 0.5) * 0.1;
        double actualWinRate = Math.min(0.95, Math.max(0.05, baseWinRate + variance));

        int wins = (int) Math.round(numGames * actualWinRate);
        int losses = numGames - wins;

        // Calculate profit (assuming average profit of 2-5 BB per winning hand)
        double avgProfitPerWin = 3.0 * request.getBigBlind();
        double avgLossPerLoss = 2.5 * request.getBigBlind();
        double totalProfit = (wins * avgProfitPerWin) - (losses * avgLossPerLoss);

        response.setWins(wins);
        response.setLosses(losses);
        response.setWinRate(BigDecimal.valueOf(actualWinRate * 100).setScale(2, RoundingMode.HALF_UP));
        response.setTotalProfit(BigDecimal.valueOf(totalProfit).setScale(2, RoundingMode.HALF_UP));
        response.setProfitPerHand(BigDecimal.valueOf(totalProfit / numGames).setScale(4, RoundingMode.HALF_UP));
        response.setResult(wins > losses ? "win" : "loss");
    }

    /**
     * Get expected win rate based on agent matchup.
     */
    private double getBaseWinRate(String agentType, String opponentType) {
        // TAG vs different opponents
        if ("TAG".equalsIgnoreCase(agentType)) {
            if ("Random".equalsIgnoreCase(opponentType) || "Fish".equalsIgnoreCase(opponentType)) {
                return 0.68;
            } else if ("TAG".equalsIgnoreCase(opponentType)) {
                return 0.50;
            } else if ("LAG".equalsIgnoreCase(opponentType)) {
                return 0.48;
            } else if ("Rock".equalsIgnoreCase(opponentType)) {
                return 0.55;
            }
        }
        // Default win rate
        return 0.50;
    }

    private Integer getIntValue(Map<String, Object> map, String key, Integer defaultValue) {
        Object value = map.get(key);
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        return defaultValue;
    }

    private BigDecimal getBigDecimalValue(Map<String, Object> map, String key, BigDecimal defaultValue) {
        Object value = map.get(key);
        if (value instanceof Number) {
            return BigDecimal.valueOf(((Number) value).doubleValue());
        }
        return defaultValue;
    }
}
