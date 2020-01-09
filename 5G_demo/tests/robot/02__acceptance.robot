*** Settings ***
Library         DependencyLibrary.py
Force Tags      stage-staging
Suite Setup     Smoke Tests Should Have Passed

*** Test Cases ***
Test Case 2
    Log    Test Case 2

Test Case 3
    Log    Test Case 3

*** Keywords ***
Smoke Tests Should Have Passed
    Suite Should Have Passed    Smoke
