# BIS ISO2 + Live API Fix Plan

## TL;DR
BIS API requires 2-letter country codes (not ISO3). Add `iso2` field to country map, convert ISO3→ISO2 before BIS calls.

## Issues Found Running Live
1. **IMF**: `+` separator → 403. **Fixed**: Changed to `,` separator.
2. **BIS**: XML not CSV. **Fixed**: Rewrote parser to use `xml.etree.ElementTree`.
3. **BIS**: Uses 2-letter codes (`US` not `USA`). **NOT FIXED** — all 48 rates return None.
4. **Country map**: Missing `iso2` field.

## Fix Tasks

### 1. Add iso2 field to country_map.py
Add `"iso2": "XX"` to each of 48 COUNTRY_MAP entries. Add `get_iso2(iso3)` function.

### 2. Update bis_fetcher.py to accept iso2
Change `fetch_policy_rate` to accept iso2 (2-letter). Update `fetch_all_policy_rates` to convert iso3→iso2 using `src.country_map.get_iso2()`.

### 3. Update CLI to pass iso2 to BIS fetcher
In `cli.py`, convert iso3 codes to iso2 before calling `fetch_all_policy_rates`.

### 4. Run full pipeline
`python -m src.cli --seed 42 --output-dir ./output`

### 5. Verify output
Check CSV has varied econ scores (not all identical mock values), Excel has correct data.

## ISO2 Mapping (48 teams)
```
MEX=MX ZAF=ZA KOR=KR CZE=CZ CAN=CA BIH=BA QAT=QA CHE=CH
BRA=BR MAR=MA HTI=HT SCO=GB USA=US PRY=PY AUS=AU TUR=TR
DEU=DE CUW=CW CIV=CI ECU=EC NLD=NL JPN=JP SWE=SE TUN=TN
BEL=BE EGY=EG IRN=IR NZL=NZ ESP=ES CPV=CV SAU=SA URY=UY
FRA=FR SEN=SN IRQ=IQ NOR=NO ARG=AR DZA=DZ AUT=AT JOR=JO
PRT=PT COD=CD UZB=UZ COL=CO GBR=GB HRV=HR GHA=GH PAN=PA
```
