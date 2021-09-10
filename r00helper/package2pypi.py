import json.decoder
import os
import shutil
import subprocess
import sys
import time
from distutils.version import StrictVersion

import requests
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import *
from r00auth import config


def get_setup_py(pypi_name, next_version, additional=None):
    setup_template_py = """from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='__dirname__',
    version='__version__',
    license='MIT',
    author="Andrey Ivanov",
    author_email='r00ft1h@gmail.com',
    packages=find_packages(),
    long_description=open(join(dirname(__file__), 'README.rst')).read(),
    {},
)"""
    if additional:
        result = setup_template_py.format(",\r\n    ".join([f"{k}={v}" for k, v in additional.items()]))
    else:
        result = setup_template_py.replace('{},', '')

    return result.replace('__dirname__', pypi_name).replace('__version__', next_version)


def get_last_version(package_name) -> str:
    """ Получает последнию версию текущего пакета """
    url = "https://pypi.org/pypi/%s/json" % (package_name,)
    r = requests.get(url)
    try:
        data = r.json()
    except json.decoder.JSONDecodeError:
        return "0.0"
    versions = data['releases'].keys()
    versions = sorted(versions, key=StrictVersion)
    last = versions[-1]
    return str(last)


def get_next_version(package_name) -> str:
    """
    Получает последнию версию текущего пакета и прибавляет к ней + 0.1
    :param package_name: Имя пакета в PyPi
    :return: float: Следуйщию версию.
    """
    last = get_last_version(package_name)
    new = round(float(last) + 0.1, 1)
    return str(new)


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.editbox = QLineEdit()
        self.initUI()

    def initUI(self):
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())
        self.setWindowTitle(' ')

        # Icon
        scriptDir = os.path.dirname(os.path.realpath(__file__))
        filepath_icon = os.path.join(scriptDir, 'source', 'pypi.png')
        self.setWindowIcon(QtGui.QIcon(filepath_icon))

        # Create desciption
        label = QLabel()
        label.setText(r"Напиши название пакета<br/>в директории I:\r00...")
        label.setStyleSheet("color: #96AE37; font: bold 14px serif;")
        label.setAlignment(Qt.AlignCenter)

        # Create input field
        self.editbox.setStyleSheet("height: 30px; background-color: #C7D97E; color: #515D1D; font: bold 14px serif; "
                                   "border-style: dotted ; border-radius: 10px; border-width: 5px; border-color: beige;")
        self.editbox.setAlignment(Qt.AlignCenter)

        # Create a button in the window
        button = QPushButton('Залить пакет на PyPi', self)
        button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        button.setStyleSheet(
            "height: 25px;\nbackground-color: #F0F0F0;\ncolor: #728168;\nfont: bold 14px serif;\nborder-style: groove;\nborder-radius: 10px;\nborder-width: 5px;\nborder-color: #C7D97E;\npadding: 0px 10px 0px 10px;\n"
            "\n"
            "}\n"
            "QPushButton:hover{    \n"
            "    background-color: #C7D97E;\n"
            "    effect = QtWidgets.QGraphicsDropShadowEffect(QPushButton)\n"
            "    effect.setOffset(0, 0)\n"
            "    effect.setBlurRadius(20)\n"
            "    effect.setColor(QColor(57, 219, 255))\n"
            "    QPushButton.setGraphicsEffect(effect)")
        button.setObjectName("pushButton")

        # Connect button to function on_click
        button.clicked.connect(self.on_click)

        # Create layout
        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addWidget(self.editbox)
        vbox.addWidget(button)
        self.setLayout(vbox)
        self.show()

    @pyqtSlot()
    def on_click(self):
        # Go package dir
        raw_text = self.editbox.text().strip().lower()
        if not raw_text:
            return self.editbox.setText('Напиши имя пакета')
        package_name = raw_text if raw_text.startswith('r00') else 'r00' + raw_text
        root_dir = 'i:\\'
        package_dir = os.path.join(root_dir, package_name)
        dist_dir = os.path.join(root_dir, package_name, 'dist')
        if not os.path.exists(package_dir):
            return self.editbox.setText('Нет такого пакета')
        os.chdir(package_dir)

        # Remove old packages tar.gz
        if os.path.exists(dist_dir):
            for filename in os.listdir(dist_dir):
                filepath = os.path.join(dist_dir, filename)
                os.remove(filepath)

        # Check paths
        pattern = '__dirname__'
        template_dir = os.path.join(root_dir, '_template')
        license_file_temp = os.path.join(template_dir, 'LICENSE.txt')
        readme_file_temp = os.path.join(template_dir, 'README.rst')
        setup_file_temp = os.path.join(template_dir, 'setup.py')
        assert os.path.exists(template_dir), f'Not found template dir: {template_dir}'
        assert os.path.exists(license_file_temp), f'Not found license file: {license_file_temp}'
        assert os.path.exists(readme_file_temp), f'Not found readme file: {readme_file_temp}'
        assert os.path.exists(setup_file_temp), f'Not found setup file: {setup_file_temp}'

        # Copy template, LICENSE.txt
        license_file_new = os.path.join(package_dir, 'LICENSE.txt')
        shutil.copy(license_file_temp, license_file_new)

        # README.rst
        readme_file_new = os.path.join(package_dir, 'README.rst')
        for temp, new in [(readme_file_temp, readme_file_new)]:
            shutil.copy(temp, new)
            with open(new) as f:
                data = f.read()
                assert pattern in data, f'Not found {pattern} in readme file'
                data_new = data.replace(pattern, package_name)
            with open(new, 'w') as f:
                f.write(data_new)

        # setup.py
        next_version = str(get_next_version(package_name))
        self.editbox.setText(f"Next version: {next_version}")
        setup_file_new = os.path.join(package_dir, 'setup.py')
        if package_name == 'r00imena':
            setup_py_data = get_setup_py(package_name, next_version, {'package_data': {'': ['*.txt']}})
        else:
            setup_py_data = get_setup_py(package_name, next_version)
        with open(setup_file_new, 'w') as f:
            f.write(setup_py_data)

        # Компилируем...
        self.editbox.setText("Компилируем...")
        subprocess.run('python setup.py sdist')

        # Заливаем на PyPi
        self.editbox.setText("Заливаем на PyPi...")
        old_version = get_last_version(package_name)
        subprocess.run(f'twine upload -u {config.pypi.login} -p {config.pypi.password} --verbose dist/*')
        t0 = time.time()
        while time.time() - t0 < 60:
            new_version = get_last_version(package_name)
            if old_version != new_version:
                break
            time.sleep(1)
        else:
            self.editbox.setText(f"ERROR upload: {new_version}")
            return False

        # Переустанавливаем пакет...
        self.editbox.setText("Переустанавливаем пакет...")
        time.sleep(5)
        t0 = time.time()
        while time.time() - t0 < 60:
            try:
                command = f'pip install --upgrade --force {package_name}=={new_version}'
                output = subprocess.check_output(command).decode()
                if f'Successfully installed {package_name}-{new_version}' in output:
                    break
            except Exception as e:
                print(command, e)
            time.sleep(3)
        else:
            self.editbox.setText(f"ERROR install upgrade: {new_version}")
            return False

        # Проверяем...
        self.editbox.setText("Проверяем...")
        output = subprocess.check_output(f'pip show {package_name}').decode().split()
        installed_version = [output[index + 1] for index, line in enumerate(output) if line == 'Version:'][0].strip()
        if installed_version == new_version:
            self.editbox.setText(f"Success! Version: {new_version}")
            print('Installed success!')
        else:
            self.editbox.setText(f"ERROR! Version: {new_version}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
