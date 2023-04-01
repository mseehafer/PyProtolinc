/**
 * @file utils.h
 * @author M. Seehafer
 * @brief Auxiliary helpers
 * @version 0.2.0
 * @date 2023-04-01
 *
 * @copyright Copyright (c) 2023
 *
 */
#ifndef C_UTILS_H
#define C_UTILS_H

#include <utility>
#include <unordered_map>

using namespace std;

/////////////////////////////////////////////////////////////////////////////////////////////
// hashing of pairs, copied from
// https://stackoverflow.com/questions/7222143/unordered-map-hash-function-c

template <class T>
inline void hash_combine(std::size_t & seed, const T & v)
{
  std::hash<T> hasher;
  seed ^= hasher(v) + 0x9e3779b9 + (seed << 6) + (seed >> 2);
}

namespace std
{
  template<typename S, typename T> struct hash<pair<S, T>>
  {
    inline size_t operator()(const pair<S, T> & v) const
    {
      size_t seed = 0;
      ::hash_combine(seed, v.first);
      ::hash_combine(seed, v.second);
      return seed;
    }
  };
}
//////////////////////////////////////////////////////////////



#endif