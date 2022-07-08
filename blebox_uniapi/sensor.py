from .feature import Feature
from typing import TYPE_CHECKING, Union, Optional

if TYPE_CHECKING:
    from .box import Box


class Sensor(Feature):
    _unit: str
    _device_class: str
    _native_value: Union[float, int, str]

    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)

    @property
    def unit(self) -> str:
        return self._unit

    @property
    def device_class(self) -> str:
        return self._device_class

    @property
    def native_value(self):
        return self._native_value

    @classmethod
    def many_from_config(cls, product, box_type_config, extended_state) -> list["Sensor"]:
        # add airSensors
        sensor_list = list()
        type_class_mapper = {
            "temperature": Temperature,
            # "wind": Wind,
            "airSensor": AirQuality
        }
        # robiera listę sensorów, wydziela im methods w zalezności o
        # utworzyc liste sensorów na podstawie extended state,
        # powinien implementodwać odpowiednią klasę dla danego typu urządenia,
        # modyfikować methods aby utrzymywać id obiektu(methods to path po drzewie do wartosci)
        print(f"UNIAPI.mfc.sensor.interface:\nprod:{product}\nbox_tc:{box_type_config}\nestate:{extended_state}")
        s_li = list()
        if extended_state:
            print("MFC_sensor:\n", extended_state, "\n", box_type_config, "\n")
            alias, methods = box_type_config[0]
            sensor_list = extended_state.get("multiSensor", {}).get("sensors", {})
            try:
                for sensor in sensor_list:
                    print("Sensor:",sensor,"\n")
                    sensor_type = sensor.get("type")
                    sensor_id = sensor.get("id")

                    if type_class_mapper.get(sensor_type):
                        value_method = {sensor_type: methods[sensor_type](sensor_id)}
                        s_li.append(type_class_mapper[sensor_type](product=product, alias=sensor_type + "_" + str(sensor_id), methods=value_method))
                        print("s_type:", sensor_type, "s_id:", sensor_id, "s_v_method:", value_method)
                return s_li
            except Exception as ex:
                print("Error YOU MF:", ex.args)
                return []
        else:
            #type clas mapper z boxtypeconfig
            alias, methods = box_type_config[0]
            if "air" in alias:
                method_li = [method for method in methods if "value" in method]
                print("method_li:",method_li)
                for method in method_li:
                    print(method, "\n")
                    alias=method.split('.')[0]
                    s_li.append(AirQuality(product=product, alias=alias, methods=methods))

                return s_li
            if "temperature" in alias:
                print("box_type_config_type", type(box_type_config),"\nAlias:", alias, "\nMethods:", methods)

                return [Temperature(product=product, alias=alias, methods=methods)]

        # todo add  _read_state_value(self)

    def read_value(self, field: str) -> Union[float, int, None]:
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value(field)
            if raw is not None:
                alias = self._alias
                return round(product.expect_int(alias, raw, 12500, -5500) / 100.0, 1)
        return None

    def after_update(self) -> None:
        self._native_value = self.read_value(self._device_class + ".value")


class Temperature(Sensor):
    _current: Union[float, int, None]

    def __init__(self, product: "Box", alias: str, methods: dict):
        self._unit = "celsius"
        self._device_class = "temperature"
        super().__init__(product, alias, methods)

    @property
    def current(self) -> Union[float, int, None]:
        return self._current

    # TODO: use as attribute in product config
    def _read_temperature(self, field: str) -> Union[float, int, None]:
        product = self._product
        # print("Temperature._read_temperature", product.last_data)
        if product.last_data is not None:
            raw = self.raw_value(field)
            if raw is not None:  # no reading
                alias = self._alias
                return round(product.expect_int(alias, raw, 12500, -5500) / 100.0, 1)
        return None

    def after_update(self) -> None:
        self._current = self._read_temperature("temperature")
        self._native_value = self._read_temperature("temperature")

# class Wind(Sensor):
#     def __init__(self, product: "Box", alias: str, methods: dict):
#         self._unit = "m/s"
#         self._device_class = "wind"
#         super().__init__(product, alias, methods)
#
#     def after_update(self) -> None:
#         self._current = self.raw_value("wind")


class AirQuality(Sensor):
    _pm: Optional[int]

    def __init__(self, product: "Box", alias: str, methods: dict):
        super().__init__(product, alias, methods)
        self._unit = "concentration_of_mp"
        self._device_class = alias
        # @property

    def _pm_value(self, name: str) -> Optional[int]:
        product = self._product
        if product.last_data is not None:
            raw = self.raw_value(name)
            if raw is not None:  # no reading
                alias = self._alias
                return product.expect_int(alias, raw, 3000, 0)
        return None

    def after_update(self) -> None:
        self._native_value = self._pm_value(self.device_class+".value")


# todo Implement new many_from_host basing on extended state(each class initialising basing on: for each sensor in sensors: type:---
# to set device_class, native_unit_of_measurment, state class
