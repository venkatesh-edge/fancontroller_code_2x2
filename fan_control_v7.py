import sys
import serial
import time
import serial.tools.list_ports
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt

# Initialize serial connection
# ser = serial.Serial('COM32', 9600, timeout=1)
# time.sleep(2)  # Allow some time to establish connection


class Dashboard(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()
        # Initialize variables with default values
        self.sensor_a_temp = 0.0
        self.fan_a1_rpm = 0
        self.fan_a2_rpm = 0
        self.sensor_b_temp = 0.0
        self.fan_b1_rpm = 0
        self.fan_b2_rpm = 0
        self.current_switch_value = "00 Hrs: 00 Min: 00 Sec"  # Initialize current switch value

        # Timer for reading serial data
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.read_serial_data)
        self.timer.start(50)  # Read data every 100 ms
        self.ser = None
        self.last_sent_mode = None  # Track last sent mode

    def initUI(self):
        self.setWindowTitle(" ")
        self.setGeometry(300, 300, 400, 400)  # Adjusted size to 150x150
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        self.adjustSize()
        self.setFixedSize(self.size())

        title_label = QtWidgets.QLabel("Fan Control Dashboard", self)
        title_label.setAlignment(QtCore.Qt.AlignCenter)  # Center the text
        title_label.setFont(QtGui.QFont("Arial", 16, QtGui.QFont.Bold))  # Set bold font and size
        title_label.setStyleSheet("color: #0066ff;")  # Change text color to blue

        # Load the Seven Segment font
        font_id = QtGui.QFontDatabase.addApplicationFont("seven_segment.ttf")
        font_family = QtGui.QFontDatabase.applicationFontFamilies(font_id)[0]
        seven_segment_font = QtGui.QFont(font_family, 12, QtGui.QFont.Bold)  # Reduced font size for compactness

        # Layouts
        main_layout = QtWidgets.QVBoxLayout()
        # main_layout.setContentsMargins(5, 5, 5, 5)  # Remove margins
        main_layout.setSpacing(2)  # Reduce spacing between elements

        com_select_frame = QtWidgets.QFrame(self)
        com_select_frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        com_select_layout = QtWidgets.QHBoxLayout(com_select_frame)

        self.com_select_label = QtWidgets.QLabel("Select port : ")
        self.com_select_label.setFont(QtGui.QFont("Arial", 9, QtGui.QFont.Bold))
        self.com_select_combo_box = QtWidgets.QComboBox()
        self.com_select_combo_box.setFont(QtGui.QFont("Arial", 9))
        self.com_select_button = QtWidgets.QPushButton("Connect")
        self.com_select_button.setFont(QtGui.QFont("Arial", 9))
        self.com_select_button.clicked.connect(self.connect_port)

        self.update_com_ports()

        com_select_layout.addWidget(self.com_select_label)
        com_select_layout.addWidget(self.com_select_combo_box)
        com_select_layout.addWidget(self.com_select_button)


        # Frame for Current Switch
        # current_switch_frame = QtWidgets.QFrame(self)
        # current_switch_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        # current_switch_layout = QtWidgets.QVBoxLayout(current_switch_frame)
        # current_switch_layout.setContentsMargins(5, 5, 5, 5)  # Remove margins
        # current_switch_layout.setSpacing(1)  # Reduce spacing

        # self.current_switch_label_text = QtWidgets.QLabel("Switch Time:")
        # self.current_switch_label_value = QtWidgets.QLabel("00 Hrs: 00 Min: 00 Sec")
        # self.current_switch_label_value.setFont(seven_segment_font)
        # current_switch_layout.addWidget(self.current_switch_label_text, alignment=QtCore.Qt.AlignCenter)
        # current_switch_layout.addWidget(self.current_switch_label_value, alignment=QtCore.Qt.AlignCenter)

        # Frame for Sensors and Fans
        sensors_frame = QtWidgets.QFrame(self)
        sensors_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        sensors_layout = QtWidgets.QHBoxLayout(sensors_frame)
        sensors_layout.setContentsMargins(5, 5, 5, 5)  # Remove margins
        sensors_layout.setSpacing(2)  # Reduce spacing

        # Sensor A Column
        sensor_a_layout = QtWidgets.QVBoxLayout()
        sensor_a_layout.setContentsMargins(5, 5, 5, 5)  # Remove margins
        sensor_a_layout.setSpacing(2)  # Reduce spacing

        self.front_label = QtWidgets.QLabel("Front")
        font = QtGui.QFont("Arial", 14)
        font.setBold(True)  # Make the font bold
        font.setUnderline(True)  # Underline the text
        self.front_label.setFont(font)
        self.front_label.setAlignment(QtCore.Qt.AlignCenter)
        self.front_label.setStyleSheet("color: #003300;")

        self.sensor_a_label_text = QtWidgets.QLabel("Temp: ")
        self.sensor_a_label_text.setFont(QtGui.QFont("Arial", 13))  # Reduced font size
        self.sensor_a_label_value = QtWidgets.QLabel("0 °C")
        self.sensor_a_label_value.setFont(seven_segment_font)

        self.fan_a1_label_text = QtWidgets.QLabel("Fan1: ")
        self.fan_a1_label_text.setFont(QtGui.QFont("Arial", 13))  # Reduced font size
        self.fan_a1_label_value = QtWidgets.QLabel("0")
        self.fan_a1_label_value.setFont(seven_segment_font)

        self.fan_a2_label_text = QtWidgets.QLabel("Fan2: ")
        self.fan_a2_label_text.setFont(QtGui.QFont("Arial", 13))  # Reduced font size
        self.fan_a2_label_value = QtWidgets.QLabel("0")
        self.fan_a2_label_value.setFont(seven_segment_font)



        # Layout for Sensor A Labels
        sensor_a_layout.addWidget(self.front_label)
        sensor_a_layout.addWidget(self.combine_labels(self.sensor_a_label_text, self.sensor_a_label_value))
        sensor_a_layout.addWidget(self.combine_labels(self.fan_a1_label_text, self.fan_a1_label_value))
        sensor_a_layout.addWidget(self.combine_labels(self.fan_a2_label_text, self.fan_a2_label_value))

        # Sensor B Column
        sensor_b_layout = QtWidgets.QVBoxLayout()
        sensor_b_layout.setContentsMargins(5, 5, 5, 5)  # Remove margins
        sensor_b_layout.setSpacing(2)  # Reduce spacing


        self.rear_label = QtWidgets.QLabel("Rear")
        font = QtGui.QFont("Arial", 14)
        font.setBold(True)  # Make the font bold
        font.setUnderline(True)  # Underline the text
        self.rear_label.setFont(font)
        self.rear_label.setAlignment(QtCore.Qt.AlignCenter)
        self.rear_label.setStyleSheet("color: #660066;")

        self.sensor_b_label_text = QtWidgets.QLabel("Temp: ")
        self.sensor_b_label_text.setFont(QtGui.QFont("Arial", 13))  # Reduced font size
        self.sensor_b_label_value = QtWidgets.QLabel("0 °C")
        self.sensor_b_label_value.setFont(seven_segment_font)

        self.fan_b1_label_text = QtWidgets.QLabel("Fan1: ")
        self.fan_b1_label_text.setFont(QtGui.QFont("Arial", 13))  # Reduced font size
        self.fan_b1_label_value = QtWidgets.QLabel("0")
        self.fan_b1_label_value.setFont(seven_segment_font)

        self.fan_b2_label_text = QtWidgets.QLabel("Fan2: ")
        self.fan_b2_label_text.setFont(QtGui.QFont("Arial", 13))  # Reduced font size
        self.fan_b2_label_value = QtWidgets.QLabel("0")
        self.fan_b2_label_value.setFont(seven_segment_font)


        # Layout for Sensor B Labels
        sensor_b_layout.addWidget(self.rear_label)
        sensor_b_layout.addWidget(self.combine_labels(self.sensor_b_label_text, self.sensor_b_label_value))
        sensor_b_layout.addWidget(self.combine_labels(self.fan_b1_label_text, self.fan_b1_label_value))
        sensor_b_layout.addWidget(self.combine_labels(self.fan_b2_label_text, self.fan_b2_label_value))

        # Add sensor layouts to main layout
        sensors_layout.addLayout(sensor_a_layout)
        sensors_layout.addLayout(sensor_b_layout)

        # Interval input section
        interval_frame = QtWidgets.QFrame(self)
        interval_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        interval_layout = QtWidgets.QVBoxLayout(interval_frame)
        interval_layout.setContentsMargins(5, 5, 5, 5)  # Remove margins
        interval_layout.setSpacing(2)  # Reduce spacing

        # Create a label for current switch value in the outer frame

        self.current_switch_label_value = QtWidgets.QLabel("00 Hrs: 00 Min: 00 Sec")
        self.current_switch_label_value.setFont(seven_segment_font)
        interval_layout.addWidget(self.current_switch_label_value, alignment=QtCore.Qt.AlignCenter)

        # Create a new frame for interval input and send button
        input_frame = QtWidgets.QFrame(interval_frame)
        input_frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        input_layout = QtWidgets.QHBoxLayout(input_frame)
        input_layout.setContentsMargins(5, 5, 5, 5)  # Remove margins
        input_layout.setSpacing(2)  # Reduce spacing

        self.interval_input = QtWidgets.QLineEdit(self)
        self.interval_input.setPlaceholderText("Set new switch time (ms)")
        self.interval_input.setFont(QtGui.QFont("Arial", 10))  # Reduced font size

        self.send_button = QtWidgets.QPushButton("Set", self)
        self.send_button.setFont(QtGui.QFont("Arial", 10))  # Reduced font size
        self.send_button.clicked.connect(self.send_interval)

        input_layout.addWidget(self.interval_input)
        input_layout.addWidget(self.send_button)

        # Add the input frame to the interval layout
        interval_layout.addWidget(input_frame)

        # # Add frames to main layout
        # main_layout.addWidget(current_switch_frame)
        main_layout.addWidget(title_label)
        main_layout.addWidget(com_select_frame, alignment=QtCore.Qt.AlignCenter)
        main_layout.addWidget(sensors_frame)
        main_layout.addWidget(interval_frame)

        # Radio buttons for Switch and Continuous modes
        mode_frame = QtWidgets.QFrame(self)
        mode_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        mode_layout = QtWidgets.QHBoxLayout(mode_frame)
        mode_layout.setContentsMargins(5, 5, 5, 5)  # Remove margins
        mode_layout.setSpacing(20)  # Reduce spacing
        mode_layout.setAlignment(QtCore.Qt.AlignCenter)

        # Radio buttons for selecting modes
        self.switch_radio_button = QtWidgets.QRadioButton("Switch Mode", self)
        self.continuous_radio_button = QtWidgets.QRadioButton("Continuous Mode", self)

        # Default to Switch mode
        self.switch_radio_button.setChecked(True)

        # Connect radio buttons to the function that sends the selected mode
        self.switch_radio_button.toggled.connect(self.send_mode)
        self.continuous_radio_button.toggled.connect(self.send_mode)

        mode_layout.addWidget(self.switch_radio_button)
        mode_layout.addWidget(self.continuous_radio_button)

        # Add mode selection frame to main layout
        main_layout.addWidget(mode_frame)

        self.setLayout(main_layout)

    def update_com_ports(self):
        """Update the list of COM ports in the combo box."""
        ports = serial.tools.list_ports.comports()
        self.com_select_combo_box.clear()  # Clear the combo box
        for port in ports:
            self.com_select_combo_box.addItem(port.device)

    def connect_port(self):
        """Establish serial connection with the selected port."""
        port = self.com_select_combo_box.currentText()
        try:
            if self.ser is not None and self.ser.is_open:
                self.ser.close()  # Close the existing connection
            self.ser = serial.Serial(port, 115200, timeout=1)
            if self.ser.is_open:
                print(f"Connected to {port}")
                self.update_com_ports()  # Refresh the COM port list
                self.com_select_combo_box.setCurrentText(port)
        except serial.SerialException as e:
            print(f"Error connecting to {port}: {e}")
            QtWidgets.QMessageBox.critical(self, "Connection Error", f"Could not connect to {port}.")


    def combine_labels(self, label_text, label_value):
        """Combines two labels (text and value) into a horizontal layout."""
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(label_text)
        hbox.addWidget(label_value)
        hbox.setAlignment(QtCore.Qt.AlignCenter)
        container = QtWidgets.QWidget()
        container.setLayout(hbox)
        return container

    def update_gui(self):
        """Update the labels with the current values."""
        self.sensor_a_label_value.setText(f"{self.sensor_a_temp:.2f} °C")
        if(self.sensor_a_temp < 55.00):
            self.sensor_a_label_value.setStyleSheet("color: green;")
        else:
            self.sensor_a_label_value.setStyleSheet("color: red;")
        self.fan_a1_label_value.setText(f"{self.fan_a1_rpm}")
        self.fan_a2_label_value.setText(f"{self.fan_a2_rpm}")

        self.sensor_b_label_value.setText(f"{self.sensor_b_temp:.2f} °C")
        if(self.sensor_b_temp < 55.00):
            self.sensor_b_label_value.setStyleSheet("color: green;")
        else:
            self.sensor_b_label_value.setStyleSheet("color: red;")
        self.fan_b1_label_value.setText(f"{self.fan_b1_rpm}")
        self.fan_b2_label_value.setText(f"{self.fan_b2_rpm}")

        # Update current switch label
        self.current_switch_label_value.setText(f"{self.current_switch_value}")
        # print(self.current_switch_value)

    def read_serial_data(self):
        """Read data from serial and update the GUI."""
        if self.ser is not None and self.ser.in_waiting > 0:
            data = self.ser.readline().decode('utf-8').strip()
            print(f"Received data: {data}")  # Print the raw data for debugging
            try:
                data_items = [item.strip() for item in data.split(',')]
                for item in data_items:
                    if "Temperature A:" in item:
                        self.sensor_a_temp = float(item.split(":")[1].strip().replace('°C', ''))
                    elif "RPM A1:" in item:
                        self.fan_a1_rpm = int(item.split(":")[1].strip())
                    elif "RPM A2:" in item:
                        self.fan_a2_rpm = int(item.split(":")[1].strip())
                    elif "Temperature B:" in item:
                        self.sensor_b_temp = float(item.split(":")[1].strip().replace('°C', ''))
                    elif "RPM B1:" in item:
                        self.fan_b1_rpm = int(item.split(":")[1].strip())
                    elif "RPM B2:" in item:
                        self.fan_b2_rpm = int(item.split(":")[1].strip())
                    elif "switch" in item:
                        self.switch_radio_button.setChecked(True)
                    elif "continuous" in item:
                        self.continuous_radio_button.setChecked(True)
                    elif "Seconds:" in item:
                        total_milliseconds = int(item.split(":")[1].strip())
                        # Convert milliseconds to seconds
                        total_seconds = total_milliseconds // 1000
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        seconds = total_seconds % 60

                        self.current_switch_value = f"Switch time  -  {hours:02d} Hrs: {minutes:02d} Min: {seconds:02d} Sec"

                        # self.current_switch_value = f"{hours:02d}Hrs: {minutes:02d}Min: {seconds:02d}Sec"

                if (self.sensor_a_temp > 60 or self.sensor_b_temp > 60) and (self.last_sent_mode != "switch" or self.last_sent_mode != "continuous") and not self.continuous_radio_button.isChecked():
                    self.ser.write("continuous\n".encode())
                    print("🔥🔥🔥🔥🔥🔥")



                self.update_gui()
            except Exception as e:
                print(f"Error parsing data: {e}")

    def send_interval(self):
        """Send the interval value to the Arduino."""
        try:

            interval_value = self.interval_input.text()  # Get the input value from the text box

            if interval_value.isdigit():  # Check if the input is a valid number

                self.ser.write(f"{interval_value}\n".encode())  # Send the value to Arduino
                print(f"Sent interval: {interval_value} ms")
                self.interval_input.clear()  # Clear the input field
            else:
                print("Invalid interval value. Please enter a numeric value.")
        except Exception as e:
            print(f"Error sending interval: {e}")

    def send_mode(self):
        """Send the selected mode (Switch or Continuous) to the Arduino."""
        try:
            if self.switch_radio_button.isChecked() and self.last_sent_mode != "switch" and (self.sensor_a_temp < 60 or self.sensor_b_temp < 60):
                self.ser.write("switch\n".encode())  # Send "switch" to Arduino
                print("Sent mode: switch")
                self.last_sent_mode = "switch"
            elif self.continuous_radio_button.isChecked() and self.last_sent_mode != "continuous":
                self.ser.write("continuous\n".encode())  # Send "continuous" to Arduino
                print("Sent mode: continuous")
                self.last_sent_mode = "continuous"
        except Exception as e:
            print(f"Error sending mode: {e}")


def main():
    app = QtWidgets.QApplication(sys.argv)
    dashboard = Dashboard()
    dashboard.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()


