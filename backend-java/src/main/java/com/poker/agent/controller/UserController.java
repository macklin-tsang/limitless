package com.poker.agent.controller;

import com.poker.agent.model.User;
import com.poker.agent.repository.UserRepository;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * REST Controller for User management.
 * Provides CRUD operations for users.
 */
@RestController
@RequestMapping("/api/users")
public class UserController {

    private final UserRepository userRepository;

    @Autowired
    public UserController(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    /**
     * Get all users.
     *
     * GET /api/users
     *
     * @return List of all users
     */
    @GetMapping
    public ResponseEntity<List<User>> getAllUsers() {
        List<User> users = userRepository.findAll();
        return ResponseEntity.ok(users);
    }

    /**
     * Get a user by ID.
     *
     * GET /api/users/{id}
     *
     * @param id the user ID
     * @return the user if found, 404 otherwise
     */
    @GetMapping("/{id}")
    public ResponseEntity<?> getUserById(@PathVariable Long id) {
        return userRepository.findById(id)
                .map(user -> ResponseEntity.ok((Object) user))
                .orElse(ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(createErrorResponse("User not found with id: " + id)));
    }

    /**
     * Create a new user.
     *
     * POST /api/users
     *
     * @param user the user to create
     * @return the created user with 201 status, or error if validation fails
     */
    @PostMapping
    public ResponseEntity<?> createUser(@Valid @RequestBody User user) {
        // Check for duplicate username
        if (userRepository.existsByUsername(user.getUsername())) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(createErrorResponse("Username already exists: " + user.getUsername()));
        }

        // Check for duplicate email
        if (userRepository.existsByEmail(user.getEmail())) {
            return ResponseEntity.status(HttpStatus.CONFLICT)
                    .body(createErrorResponse("Email already exists: " + user.getEmail()));
        }

        User savedUser = userRepository.save(user);
        return ResponseEntity.status(HttpStatus.CREATED).body(savedUser);
    }

    /**
     * Update an existing user.
     *
     * PUT /api/users/{id}
     *
     * @param id the user ID
     * @param userDetails the updated user details
     * @return the updated user, or 404 if not found
     */
    @PutMapping("/{id}")
    public ResponseEntity<?> updateUser(@PathVariable Long id, @Valid @RequestBody User userDetails) {
        return userRepository.findById(id)
                .map(existingUser -> {
                    // Check for duplicate username (excluding current user)
                    if (!existingUser.getUsername().equals(userDetails.getUsername()) &&
                            userRepository.existsByUsername(userDetails.getUsername())) {
                        return ResponseEntity.status(HttpStatus.CONFLICT)
                                .body((Object) createErrorResponse("Username already exists: " + userDetails.getUsername()));
                    }

                    // Check for duplicate email (excluding current user)
                    if (!existingUser.getEmail().equals(userDetails.getEmail()) &&
                            userRepository.existsByEmail(userDetails.getEmail())) {
                        return ResponseEntity.status(HttpStatus.CONFLICT)
                                .body((Object) createErrorResponse("Email already exists: " + userDetails.getEmail()));
                    }

                    existingUser.setUsername(userDetails.getUsername());
                    existingUser.setEmail(userDetails.getEmail());
                    User updatedUser = userRepository.save(existingUser);
                    return ResponseEntity.ok((Object) updatedUser);
                })
                .orElse(ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(createErrorResponse("User not found with id: " + id)));
    }

    /**
     * Delete a user.
     *
     * DELETE /api/users/{id}
     *
     * @param id the user ID
     * @return 204 No Content if deleted, 404 if not found
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<?> deleteUser(@PathVariable Long id) {
        return userRepository.findById(id)
                .map(user -> {
                    userRepository.delete(user);
                    return ResponseEntity.noContent().build();
                })
                .orElse(ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(createErrorResponse("User not found with id: " + id)));
    }

    /**
     * Create a standardized error response.
     */
    private Map<String, String> createErrorResponse(String message) {
        Map<String, String> error = new HashMap<>();
        error.put("error", message);
        return error;
    }
}
