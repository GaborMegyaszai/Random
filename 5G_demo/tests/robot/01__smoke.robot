*** Settings ***
Library                 Process
Library                 String
Library                 Collections
Library                 DependencyLibrary.py
Force Tags              stage-laboratory

*** Test Cases ***
Test Case 1
    Address Should Be Reachable     95.216.192.97

Failing Example
    [Tags]                          failing
    Address Should Be Reachable     240.0.0.0

*** Keywords ***
Address Should Be Reachable
    [Arguments]                     ${address}
    ${result}                       Run Process             ping        ${address}                          -c 4
    Should Be Equal As Integers     ${result.rc}            0           Ping failed:\n${result.stdout}      values=false
    Save KPIs                       ${result.stdout}

Save KPIs
    [Arguments]         ${output}
    @{lines}            Split To Lines                  ${output}           -2
    ${kpi}              Parse Stats                     @{lines}[1]
    ${loss}             Parse Packet Loss               @{lines}[0]
    Set To Dictionary   ${kpi}                          loss=${loss}
    Log Dictionary      ${kpi}

Parse Packet Loss
    [Arguments]         ${line}
    ${loss}             Remove String Using Regexp      ${line}             .*,                 %.*
    [Return]            ${loss}

Parse Stats
    [Arguments]         ${line}
    ${values}           Remove String Using Regexp      ${line}             .*=                 \ ms
    @{parsed}           Split String                    ${values}           /
    &{stats}            Create Dictionary               min=@{parsed}[0]    avg=@{parsed}[1]    max=@{parsed}[2]    stddev=@{parsed}[3]
    [Return]            ${stats}
