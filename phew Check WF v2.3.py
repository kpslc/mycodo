# 4 Nov V 2.3 - added up and down to the messages - 
# 31 Oct 2020 - Changed range for EC 750-950
# V 2.2 added changed ranges for pH 5.8-6.2 and EC 550-850
# V 2.1 added waterflow volume check before dosing chemicals

## Edit below to set desired ranges for pH and electrical conductivity ###

# Low value for water flow in liters per minute
range_wf_low = 0.2

# Desired range for electrical conductivity
range_ec_high = 950
range_ec_low = 750

# Desired range for pH
range_ph_high = 6.2
range_ph_low = 5.8

# pH range that will immediately cause a pH correction
range_ph_high_danger = 7.0
range_ph_low_danger = 5.0

### Edit below to set the IDs for Conditions and Actions ###

condition_id_measurement_ph_id = "{18a811f0}"  # Condition: measurement, last, pH Input
condition_id_measurement_ec_id = "{5d050302}"  # Condition: measurement, last, EC Input
condition_id_measurement_wf_id = "{54cb18df}"  # Condition: measurement, last, wf Input
action_id_pump_1_acid = "{4262eedc}"  # Action: Pump 1 (Acid)
action_id_pump_2_base = "{5d400167}"  # Action: Pump 2 (Base)
action_id_pump_3_nutrient_a = "{54a0ac22}"  # Action: Pump 3 (Nutrient A)
action_id_pump_4_nutrient_b = "{a1c160da}"  # Action: Pump 4 (Nutrient B)
action_id_email_notification = "{3332c9bb}"  # Action: Email Notification

### DO NOT EDIT BELOW THIS LINE UNLESS YOU KNOW WHAT YOU ARE DOING ###

import time

if 'notify_ec' not in self.variables:  # Initiate EC notification timer
    self.variables['notify_ec'] = 0
if 'notify_ph' not in self.variables:  # Initiate pH notification timer
    self.variables['notify_ph'] = 0
if 'notify_none' not in self.variables:  # Initiate None measurement notification timer
    self.variables['notify_none'] = 0
if 'notify_wf' not in self.variables:  # Initiate wf (water flow) measurement notification timer
    self.variables['notify_wf'] = 0

measure_ec = self.condition(condition_id_measurement_ec_id)
measure_ph = self.condition(condition_id_measurement_ph_id)
measure_wf = self.condition(condition_id_measurement_wf_id)  #id for water flow
self.message = ""

# self.logger.debug("Conditional check. EC: {}, pH: {}, wf: {}".format(measure_ec, measure_ph, measure_wf))
self.logger.debug("Conditional check. EC: {}, pH: {}, wf: {}".format(measure_ec, measure_ph, measure_wf))

if None in [measure_ec, measure_ph, measure_wf]:
    if measure_ec is None:
        self.message += "\nWarning: No EC Measurement! Check sensor!"
    if measure_ph is None:
        self.message += "\nWarning: No pH Measurement! Check sensor!"
    if measure_wf is None:
        self.message += "\nWarning: No Measure WF"
    if self.variables['notify_none'] < time.time():  # Only notify every 12 hours
        self.variables['notify_none'] = time.time() + 21600  # 6 hours
        self.run_action(action_id_email_notification, message=self.message)  # Email alert
    self.logger.error(self.message)
    return

if measure_wf < range_wf_low: # if water flow is less than .2 liters per hour then skip the remaining steps.
    msg = "Hydroponics water flow is dangerously low at {} liters per minute. Should be > 0.6. pH is: {}. EC is: {}. Check the water flow. No other chemical dispensing will occur till water flow is at least 0.2 liters per hour.".format(measure_wf, measure_ph, measure_ec)
    self.logger.info(msg)
    self.message += msg
    if self.variables['notify_wf'] < time.time():  # Only notify every 4 hours
        self.variables['notify_wf'] = time.time() + 1440  # 4 hours
        self.run_action(action_id_email_notification, message=self.message)  # Email alert

# next check if pH is dangerously low or high, and adjust if it is
elif measure_ph < range_ph_low_danger:  # pH dangerously low, add base (pH up)
    msg = "Hydroponics pH is dangerously low: {}. Should be > {}. Dispensing base (pH up)".format(measure_ph, range_ph_low_danger)
    self.logger.info(msg)
    self.message += msg
    self.run_action(action_id_pump_2_base)  # Dispense base (pH up)
    if self.variables['notify_ph'] < time.time():  # Only notify every 12 hours
        self.variables['notify_ph'] = time.time() + 43200  # 12 hours
        self.run_action(action_id_email_notification, message=self.message)  # Email alert
elif measure_ph > range_ph_high_danger:  # pH dangerously high, add acid (pH down)
    msg = "Hydroponics pH is dangerously high: {}. Should be < {}. Dispensing acid (pH down)".format(measure_ph, range_ph_high_danger)
    self.logger.info(msg)
    self.message += msg
    self.run_action(action_id_pump_1_acid)  # Dispense acid (pH down)
    if self.variables['notify_ph'] < time.time():  # Only notify every 12 hours
        self.variables['notify_ph'] = time.time() + 43200  # 12 hours
        self.run_action(action_id_email_notification, message=self.message)  # Email alert

# If pH isn't dangerously low or high, check if EC is within range
elif measure_ec < range_ec_low:  # EC too low, add nutrient
    self.logger.info("EC: {}. Should be > {}. Dispensing Nutrient A and B".format(measure_ec, range_ec_low))
    self.run_action(action_id_pump_3_nutrient_a)  # Dispense nutrient A
    self.run_action(action_id_pump_4_nutrient_b)  # Dispense nutrient B
elif measure_ec > range_ec_high:  # EC too high, add water
    msg = "Hydroponics EC: {}. Should be < {}. Need to add water to dilute!".format(measure_ec, range_ec_high)
    self.logger.info(msg)
    if self.variables['notify_ec'] < time.time():  # Only notify every 12 hours
        self.variables['notify_ec'] = time.time() + 43200  # 12 hours
        self.message += msg
        self.run_action(action_id_email_notification, message=self.message)  # Email alert

# If EC is in range, make sure pH is within range
elif measure_ph < range_ph_low:  # pH too low, add base (pH up)
    self.logger.info("EC is okay at {}. pH is {}. It should be > {}. Dispensing base (pH up)".format(measure_ec, measure_ph, range_ph_low))
    self.run_action(action_id_pump_2_base)  # Dispense base (pH up)
elif measure_ph > range_ph_high:  # pH too high, add acid (pH down)
    self.logger.info("EC is okay at {}. pH is {}. Should be < {}. Dispensing acid (pH down)".format(measure_ec, measure_ph, range_ph_high))
    self.run_action(action_id_pump_1_acid)  # Dispense acid (pH down)
# else: # EC and PH are okay
    # self.logger.info("EC and pH are okay")
    # self.message = "EC and pH are okay"
    # self.run_action(action_id_email_notification, message=self.message)  # Email alert
