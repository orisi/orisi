import json

PREGENERATED_ADDRESSES_JSON = """{
    "client_pubkey": "02997bd658fe9df0706596e341a2fa8d2ac58111a88c0b7afa0fc3a7b9e32d4f5c",
    "client_address": "12GyMKmujGuR1pwAWDiNoMGcnsBNhKwav3",
    "oracles": [
        {
            "address": "1GKwKyRqB4tURDFvsEG5Hfr6ApWhNRzQE8",
            "pubkey": "023a3d2bd4180795ec49e87da2fe0d46a8277e6e3e1a3eea7bdf07d0a67280d4c3"
        },
        {
            "address": "1EW3MmorEEVeesvCvyUCSfvJzeMJsmicaB",
            "pubkey": "02e959a1df8864198b52b575442e491d66e46b5eab157b0e352b381c3ee00a6251"
        },
        {
            "address": "14Sf5m5TxY21ziw8QYJKPDyB1YzCmGpM8q",
            "pubkey": "027c84bb303036b9fdd25e0968aeb939036bdbdeff78693048c594119f4026c489"
        },
        {
            "address": "1K9HYc64rETcgHByquCDhMXu9giuGuDGzy",
            "pubkey": "0345191972281f8c3b8303861fec59fc6b9b21c8754a047aed3f9f52fc015cacbd"
        },
        {
            "address": "19ie62GP2hbsZBnHTiQzs13tW65gpz3Wig",
            "pubkey": "0390319cf7c02b23d3c6cd29c0607f8e30c72fbbe6d4eeea2a9c74b8f525584631"
        }
    ]
}"""

ADDRESSES = json.loads(PREGENERATED_ADDRESSES_JSON)
