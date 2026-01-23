package com.poker.agent;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.poker.agent.model.User;
import com.poker.agent.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import static org.hamcrest.Matchers.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for UserController.
 * Uses H2 in-memory database for testing.
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
public class UserControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        userRepository.deleteAll();
    }

    @Test
    void getAllUsers_EmptyDatabase_ReturnsEmptyList() throws Exception {
        mockMvc.perform(get("/api/users"))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$", hasSize(0)));
    }

    @Test
    void getAllUsers_WithUsers_ReturnsUserList() throws Exception {
        // Create test users
        User user1 = new User("alice", "alice@example.com");
        User user2 = new User("bob", "bob@example.com");
        userRepository.save(user1);
        userRepository.save(user2);

        mockMvc.perform(get("/api/users"))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$", hasSize(2)))
                .andExpect(jsonPath("$[0].username", is("alice")))
                .andExpect(jsonPath("$[1].username", is("bob")));
    }

    @Test
    void getUserById_ExistingUser_ReturnsUser() throws Exception {
        User user = new User("charlie", "charlie@example.com");
        User savedUser = userRepository.save(user);

        mockMvc.perform(get("/api/users/" + savedUser.getId()))
                .andExpect(status().isOk())
                .andExpect(content().contentType(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.id", is(savedUser.getId().intValue())))
                .andExpect(jsonPath("$.username", is("charlie")))
                .andExpect(jsonPath("$.email", is("charlie@example.com")))
                .andExpect(jsonPath("$.createdAt", notNullValue()));
    }

    @Test
    void getUserById_NonExistentUser_Returns404() throws Exception {
        mockMvc.perform(get("/api/users/999"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error", containsString("User not found")));
    }

    @Test
    void createUser_ValidUser_ReturnsCreatedUser() throws Exception {
        User newUser = new User("dave", "dave@example.com");

        mockMvc.perform(post("/api/users")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(newUser)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id", notNullValue()))
                .andExpect(jsonPath("$.username", is("dave")))
                .andExpect(jsonPath("$.email", is("dave@example.com")))
                .andExpect(jsonPath("$.createdAt", notNullValue()));
    }

    @Test
    void createUser_DuplicateUsername_Returns409() throws Exception {
        User existingUser = new User("eve", "eve@example.com");
        userRepository.save(existingUser);

        User duplicateUser = new User("eve", "different@example.com");

        mockMvc.perform(post("/api/users")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(duplicateUser)))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.error", containsString("Username already exists")));
    }

    @Test
    void createUser_DuplicateEmail_Returns409() throws Exception {
        User existingUser = new User("frank", "frank@example.com");
        userRepository.save(existingUser);

        User duplicateUser = new User("different", "frank@example.com");

        mockMvc.perform(post("/api/users")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(duplicateUser)))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.error", containsString("Email already exists")));
    }

    @Test
    void createUser_InvalidUsername_ReturnsBadRequest() throws Exception {
        String invalidUserJson = "{\"username\":\"\",\"email\":\"valid@example.com\"}";

        mockMvc.perform(post("/api/users")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(invalidUserJson))
                .andExpect(status().isBadRequest());
    }

    @Test
    void createUser_InvalidEmail_ReturnsBadRequest() throws Exception {
        String invalidUserJson = "{\"username\":\"validuser\",\"email\":\"not-an-email\"}";

        mockMvc.perform(post("/api/users")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(invalidUserJson))
                .andExpect(status().isBadRequest());
    }

    @Test
    void updateUser_ExistingUser_ReturnsUpdatedUser() throws Exception {
        User user = new User("george", "george@example.com");
        User savedUser = userRepository.save(user);

        User updatedDetails = new User("george_updated", "george_updated@example.com");

        mockMvc.perform(put("/api/users/" + savedUser.getId())
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(updatedDetails)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.username", is("george_updated")))
                .andExpect(jsonPath("$.email", is("george_updated@example.com")));
    }

    @Test
    void updateUser_NonExistentUser_Returns404() throws Exception {
        User updatedDetails = new User("nobody", "nobody@example.com");

        mockMvc.perform(put("/api/users/999")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(updatedDetails)))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error", containsString("User not found")));
    }

    @Test
    void deleteUser_ExistingUser_Returns204() throws Exception {
        User user = new User("henry", "henry@example.com");
        User savedUser = userRepository.save(user);

        mockMvc.perform(delete("/api/users/" + savedUser.getId()))
                .andExpect(status().isNoContent());

        // Verify user is deleted
        mockMvc.perform(get("/api/users/" + savedUser.getId()))
                .andExpect(status().isNotFound());
    }

    @Test
    void deleteUser_NonExistentUser_Returns404() throws Exception {
        mockMvc.perform(delete("/api/users/999"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error", containsString("User not found")));
    }
}
