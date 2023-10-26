#!/usr/bin/env python3
from argparse import ArgumentParser
import tqdm
import can  # Zmieniamy sposób importu na "can"
from can import Notifier
from tp20 import TP20Transport
from kwp2000 import KWP2000Client, ECU_IDENTIFICATION_TYPE
from ccp import CcpClient, BYTE_ORDER

CHUNK_SIZE = 4

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--bus", default="slcan", help="CAN interface type")  # Zmieniamy interfejs CAN na "slcan"
    parser.add_argument("--channel", default="COM15@1000000", help="CAN channel and parameters")
    parser.add_argument("--start-address", default=0, type=int, help="start address")
    parser.add_argument("--end-address", default=0x5FFFF, type=int, help="end address (inclusive)")
    parser.add_argument("--output", required=True, help="output file")
    args = parser.parse_args()

    # Inicjalizacja interfejsu CAN
    bus = can.interface.Bus(interface=args.bus, channel=args.channel, bitrate=500000)

    print("Connecting using KWP2000...")
    tp20 = TP20Transport(bus, 0x9)
    kwp_client = KWP2000Client(tp20)

    print("Reading ecu identification & flash status")
    ident = kwp_client.read_ecu_identifcation(ECU_IDENTIFICATION_TYPE.ECU_IDENT)
    print("ECU identification", ident)

    status = kwp_client.read_ecu_identifcation(ECU_IDENTIFICATION_TYPE.STATUS_FLASH)
    print("Flash status", status)
	
    print("\nConnecting using CCP...")
    client = CcpClient(bus, 1746, 1747, byte_order=BYTE_ORDER.LITTLE_ENDIAN)
    client.connect(0x0)


    progress = tqdm.tqdm(total=args.end_address - args.start_address)

    addr = args.start_address
    client.set_memory_transfer_address(0, 0, addr)

    with open(args.output, "wb") as f:
        while addr < args.end_address:
            f.write(client.upload(CHUNK_SIZE)[:CHUNK_SIZE])
            f.flush()

            addr += CHUNK_SIZE
            progress.update(CHUNK_SIZE)
