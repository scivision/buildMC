cmake_minimum_required(VERSION 3.0)
project(CMakeAPIdemo LANGUAGES NONE)
enable_testing()

option(full "do all langauge tests" OFF)

include(CheckLanguage)

check_language(C)
if(CMAKE_C_COMPILER)
  enable_language(C)
  add_executable(minimal_c src/minimal.c)
  add_test(NAME Minimal_C COMMAND minimal_c)
endif()


if(full)

check_language(CXX)
if(CMAKE_CXX_COMPILER)
  enable_language(CXX)
  add_executable(minimal_cxx src/minimal.cxx)
  add_test(NAME Minimal_CXX COMMAND minimal_cxx)
endif()

check_language(Fortran)
if(CMAKE_Fortran_COMPILER)
  enable_language(Fortran)
  add_executable(minimal_fortran src/minimal.f90)
  add_test(NAME Minimal_Fortran COMMAND minimal_fortran)
endif()

check_language(CSharp)
if(CMAKE_CSharp_COMPILER)
  enable_language(CSharp)
  add_executable(minimal_cs src/minimal.cs)
  add_test(NAME Minimal_CSharp COMMAND minimal_csharp)
endif()

check_language(Swift)
if(CMAKE_Swift_COMPILER)
  enable_language(Swift)
  add_executable(minimal_swift src/minimal.swift)
  add_test(NAME Minimal_Swift COMMAND minimal_swift)
endif()

endif(full)
