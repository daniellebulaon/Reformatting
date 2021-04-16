from opentrons import protocol_api
from opentrons.types import Location

metadata = {

    'protocolName': 'V2 Reformatting 10,15mL Tubes 1-to-5 2x105 JL_DB Edits',
    'author': 'Nick Diehl',
    'apiLevel': '2.9'
}


def run(protocol: protocol_api.ProtocolContext):
    #Lights prep
    gpio = protocol._hw_manager.hardware._backend._gpio_chardev

    #labware
    rack1 = protocol.load_labware('nest_32_tuberack_8x15ml_8x15ml_8x15ml_8x15ml', '1')
    # rack2 = protocol.load_labware('nest_32_tuberack_8x15ml_8x15ml_8x15ml_8x15ml','4')
    # rack3 = protocol.load_labware('nest_32_tuberack_8x15ml_8x15ml_8x15ml_8x15ml','7')
    tuberacks = [rack1]
    tiprack_1000_1 = protocol.load_labware('opentrons_96_tiprack_1000ul','10')
    empty_tiprack_1000 = protocol.load_labware('opentrons_96_filtertiprack_1000ul','11')
    deepwell_96 = protocol.load_labware('nest_96_wellplate_2ml_deep','3')

    #Pipettes
    r_p = protocol.load_instrument('p1000_single_gen2','right',tip_racks=[tiprack_1000_1])

    # Mapping of Wells
    sources = [well for rack in tuberacks[::-1] for row in rack.rows()[:0:-1] for well in row[::-1]]
    destination_sets = [row[i*5:i*5+5] for i in range(3) for row in deepwell_96.rows()[::-1]]

    #Pipette max_speeds
    r_p.flow_rate.aspirate = 400
    r_p.flow_rate.dispense = 400
    r_p.flow_rate.blow_out = 400

    tip_droptip_count = 0
    tip_pickup_count = 0

    #Light turns to yellow to indicate protocol is running
    gpio.set_button_light(red=True, green=True, blue=False)

    #Pipetting Actions
    for source, dest_set in zip(sources, destination_sets):
        r_p.pick_up_tip(tiprack_1000_1.wells()[tip_pickup_count])
        
        #dispense round 1
        r_p.aspirate(550, source.top(-92))
        r_p.air_gap(20)

        for i, dest in enumerate(dest_set):  # go through the entries for each tube
            disp_vol = 10 + 105 if i == 0 else 105
            tip_pickup_count += 1

            r_p.dispense(disp_vol, dest.bottom(5))
            r_p.touch_tip(v_offset=-6, speed=40)

        #dispense round 2
        r_p.aspirate(500, source.top(-92))
        r_p.air_gap(20)

        for i, dest in enumerate(dest_set):  # go through the entries for each tube
            disp_vol = 10 + 105 if i == 0 else 105

            r_p.dispense(disp_vol, dest.bottom(5))
            r_p.touch_tip(v_offset=-6, speed=40)
        
        
        #Home the Z/A mount. Not the pipette
        r_p.air_gap(100)  # aspirate any liquid that may be leftover inside the tip
        protocol._implementation.get_hardware().hardware.home_z(r_p._implementation.get_mount())
        current_location = protocol._implementation.get_hardware().hardware.gantry_position(r_p._implementation.get_mount())
        final_location_xy = current_location._replace(y=300,x=300)
        r_p.move_to(Location(labware=None, point=final_location_xy),force_direct=True)

        r_p.drop_tip(empty_tiprack_1000.wells()[tip_droptip_count])
        tip_droptip_count += 1

    gpio.set_button_light(red=False, green=True, blue=False)
    protocol.pause()
    protocol.home()
    gpio.set_button_light(red=False, green=False, blue=True)
