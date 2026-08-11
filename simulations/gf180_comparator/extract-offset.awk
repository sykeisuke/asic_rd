/trip_diff/ { trip = $3 }
END {
    if (trip == "") exit 1
    printf "%.3f,%.9g\n", common_mode, trip
}
