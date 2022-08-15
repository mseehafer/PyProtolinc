cmake_minimum_required(VERSION 2.8)

project(tests)

add_executable(${PROJECT_NAME} test_calculations.cpp)

#set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11 -pthread")

target_link_libraries(${PROJECT_NAME} PUBLIC
#calculations

gtest

gtest_main
)