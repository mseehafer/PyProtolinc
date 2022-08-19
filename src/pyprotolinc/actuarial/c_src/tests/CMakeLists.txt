#cmake_minimum_required(VERSION 2.8)
cmake_minimum_required(VERSION 3.5)


project(test_it)
#enable_testing()

#set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11 -pthread")


find_package(GTest CONFIG REQUIRED)
add_executable(tests test_calculations.cpp test_time_axis.cpp)

# target_link_libraries(tests PUBLIC GTest::gmock GTest::gtest GTest::gmock_main GTest::gtest_main)
target_link_libraries(tests PUBLIC GTest::gtest GTest::gtest_main)
#add_test(test-1 tests)

#target_link_libraries(${PROJECT_NAME} PUBLIC
##calculations
#gtest
#gtest_main
#)