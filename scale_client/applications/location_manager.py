from scale_client.core.application import Application
from scale_client.core.sensed_event import SensedEvent

import time
import logging
log = logging.getLogger(__name__)

class LocationManager(Application):
	"""
	LocationManager collects location information from location providers
	such as GPS, Geo IP service, etc.

	It reports location changes to other components for them to tag SensedEvent
	"""
	def __init__(self, broker):
		Application.__init__(broker)

		# Keep location coordinates and its time-stamp, associated with source
		# Format: device: {"lat": , "lon": , "alt": , "expire": , "priority": }
		self._location_pool = {}

	SOURCE_SUPPORT = ["geo_ip"]

	def _on_event(self, event, topic):
		"""
		LocationManager should deal with all location events published by
		location providers.
		"""
		#Analyze event
		et = event.get_type()
		data = event.get_raw_data()
		if not et in LocationManager.SOURCE_SUPPORT:
			return
		item = {"lat": data["lat"],
			"lon": data["lon"],
			"alt": None,
			"expire": data["exp"],
			"priority": event["priority"]}
		self._location_pool[event.device] = item

		#Update location pool and choose a best location to report
		best_device = self._update_location()

		#Publish the best location
		if not best_device:
			return
		up = SensedEvent(sensor = "location",
				data = self._location_pool[best_device],
				priority = 5)
		self.publish(up)
		pass

	def _update_location(self):
		"""
		Remove expired location
		Return location with the highest priority
		"""
		best_device = None
		highest_pri = None

		for device in self._location_pool:
			if self._location_pool[device]["expire"] < time.time():
				self._location_pool.pop(device, None)
			if best_device is None or self._location_pool[device]["priority"] < highest_pri:
				best_device = device
				highest_pri = self._location_pool[device]["priority"]

		return best_device

