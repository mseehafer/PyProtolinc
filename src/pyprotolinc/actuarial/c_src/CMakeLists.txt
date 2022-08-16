cmake_minimum_required(VERSION 2.8)

project(PyProtolincCore)

find_package(GTest CONFIG REQUIRED)

#include(${CMAKE_SOURCE_DIR}/conanbuildinfo.cmake)
#conan_basic_setup()

add_subdirectory(tests)


#set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")
#set(CONAN_DISABLE_CHECK_COMPILER "1")


# add_subdirectory(modules)

# add_executable(${PROJECT_NAME} mainapp.cpp)
# target_link_libraries(${PROJECT_NAME} calculations)
