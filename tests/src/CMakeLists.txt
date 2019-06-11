cmake_minimum_required(VERSION 3.0)
project(CMakeAPIdemo LANGUAGES NONE)

include(CheckLanguage)

check_language(C)
if(CMAKE_C_COMPILER)
  enable_language(C)
  add_executable(minimal minimal.c)
endif()

check_language(CXX)
if(CMAKE_CXX_COMPILER)
  enable_language(CXX)
endif()

check_language(Fortran)
if(CMAKE_Fortran_COMPILER)
  enable_language(Fortran)
endif()