import sys
import yaml
import cmd
import hid
from tabulate import tabulate

global conf


class GorbDriver(cmd.Cmd):
    intro = "\nwelcome to gorb driver tool. \ntype help to get how to use."
    prompt = "\ngorb> "

    open_device = None

    def do_help(self, args):
        return super().do_help(args)

    def do_list(self, args):
        """list all hid device from gorb"""

        table_data = []
        for idx, dev in enumerate(hid.enumerate(), start=0):
            if dev.get("manufacturer_string", "") == conf["manufacturer"]:
                row = [
                    idx,
                    dev.get("product_id", "N/A"),
                    dev.get("product_string", "N/A"),
                    dev.get("usage", "N/A"),
                    dev.get("path", "N/A"),
                    "usb",
                ]
                table_data.append(row)

        headers = ["idx", "product_id", "product_string", "usage", "path", "type"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

    def do_connect(self, args):
        """connect specified device to do command.\nusage: connect <device_id>"""
        try:
            idx = int(args, 0)

            if self.open_device:
                print(f"there is already exists a connect")
                return

            dev = hid.enumerate()[idx]

            if dev.get("manufacturer_string", "") != conf["manufacturer"]:
                print(f"error idx")
                return

            self.open_device = hid.device()
            self.open_device.open_path(dev["path"])

            print(f"connected to: {self.open_device.get_product_string()} ")
        except ValueError:
            print("invalid params\nusage: connect <device_id>")
        except Exception as e:
            print(f"connect failed: {e}")

    def do_disconnect(self, args):
        """disconnect current device.\nusage: disconnect"""
        if not self.open_device:
            print(f"there is not connect exists")
            return

        self.open_device.close()
        self.open_device = None

    def do_setdpi(self, args):
        """send setdpi command to connected device.\t dpi should >= 50 and <= 26000.\nusage: setdpi <dpi value>"""
        try:
            if not self.open_device:
                print(f"there is not connect exists")
                return

            dpi = int(args, 0)
            dpi = min(26000, max(dpi, 50))

            buffer = bytes([0x00, 0x02, dpi & 0xFF, (dpi >> 8) & 0xFF])
            ret = self.open_device.write(buffer)

            if ret == -1:
                print(f"setdpi error : {self.open_device.error()}")
            else:
                print(f"setdpi success : {dpi}")
        except ValueError:
            print("invalid params\nusage: setdpi <dpi value>")
        except Exception as e:
            print(f"setdpi failed: {e}")

    def do_macro(self, args):
        """
        send macro command to connected device.
        usage: macro <delta axis_x> <delta axis_y> <button bits>.
        example:
        move left 10px, down 10px. press leftbtn and rightbtn: macro 10 10 11000000 or macro 10 10 11
        """
        try:
            if not self.open_device:
                print(f"there is not connect exists")
                return

            params = args.split()
            x_str = params[0]
            y_str = params[1]
            
            button_str = len(params) > 2 and params[2] or None

            x = int(x_str, 0)
            y = int(y_str, 0)

            button = 0

            if button_str:
                if len(button_str) > 8:
                    button_str = button_str[:8]
                else:
                    button_str = button_str.rjust(8, "0")

                button = int(button_str, 2)

            buffer = bytes(
                [
                    0x00,
                    0x03,
                    x & 0xFF,
                    (x >> 8) & 0xFF,
                    y & 0xFF,
                    (y >> 8) & 0xFF,
                    button,
                ]
            )
            ret = self.open_device.write(buffer)

            if ret == -1:
                print(f"send macro error : {self.open_device.error()}")
            else:
                print(f"send macro success : {x} {y}")
        except ValueError:
            print("invalid params\nusage: macro <delta axis_x> <delta axis_y> <button bits>.")
        except Exception as e:
            print(f"setdpi failed: {e}")


if __name__ == "__main__":
    print(f"loading.....")

    with open("conf.yaml", "r", encoding="utf-8") as f:
        conf = yaml.safe_load(f)

    try:
        GorbDriver().cmdloop()
    except KeyboardInterrupt:
        print("bye!")
        sys.exit(0)
