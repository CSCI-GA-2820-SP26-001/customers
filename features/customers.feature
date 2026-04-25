Feature: Customer Service REST API
  As a Customer Service manager
  I need a RESTful customer service
  So that I can manage my customers

  Background:
    Given the server is running

  Scenario: The server returns a healthy status
    When I visit the "health" endpoint
    Then the response status code should be 200
    And the response should contain "OK"

  Scenario: Create a new customer
    When I create a customer with the following data
      | name    | userid   | email                |
      | Alice   | alice01  | alice@example.com    |
    Then the response status code should be 201
    And the response should contain "Alice"

  Scenario: Read an existing customer
    Given a customer exists with name "Bob", userid "bob01", email "bob@example.com"
    When I retrieve the customer by id
    Then the response status code should be 200
    And the response should contain "Bob"

  Scenario: List all customers
    When I request the list of customers
    Then the response status code should be 200
    And the response should be a list

  Scenario: Delete a customer
    Given a customer exists with name "Carol", userid "carol01", email "carol@example.com"
    When I delete the customer by id
    Then the response status code should be 204

  Scenario: Update an existing customer
    Given a customer exists with name "Dave", userid "dave01", email "dave@example.com"
    When I update the customer with the following data
      | name         | userid  | email             |
      | Dave Updated | dave01  | dave@example.com  |
    Then the response status code should be 200
    And the response should contain "Dave Updated"

  Scenario: Query customers by name
    Given a customer exists with name "Eve", userid "eve01", email "eve@example.com"
    When I query customers by name "Eve"
    Then the response status code should be 200
    And the response should be a list
    And the response should contain "Eve"

  Scenario: Activate a customer
    Given a customer exists with name "Frank", userid "frank01", email "frank@example.com"
    When I activate the customer by id
    Then the response status code should be 200
    And the response should contain "true"
