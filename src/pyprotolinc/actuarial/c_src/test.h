

// cpp header
enum class State: int
{
    Good,
    Bad,
    Unknown,
};


const char* foo(State s){
    switch (s){
        case State::Good:
            return "Good";
        case State::Bad:
            return "Bad";
        case State::Unknown:
            return "Unknown";
    }
}