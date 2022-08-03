/* CPP implementation of the risk factors. */

#ifndef C_RISK_FACTORS_H
#define C_RISK_FACTORS_H

enum class CRiskFactors: int {
    Age,                                // 0
    Gender,                             // 1
    CalendarYear,                       // 2
    SmokerStatus,                       // 3
    YearsDisabledIfDisabledAtStart,     // 4
};


const char* CRiskFactors_names(CRiskFactors rf){
    switch (rf){
        case CRiskFactors::Age:
            return "Age";
        case CRiskFactors::Gender:
            return "Gender";
    }
}

#endif