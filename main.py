import dearpygui.dearpygui as dpg
import numpy as np
from core import Core


def research(from_db, to_db, step_db, repeat_count):
    sampling_frequency = dpg.get_value("sampling_frequency")
    sequence_length = dpg.get_value("sequence_length")
    baud_rate = dpg.get_value("baud_rate")
    carrier_frequency = dpg.get_value("carrier_frequency")
    snr = dpg.get_value("snr")
    enable_noise = dpg.get_value("enable_noise")

    core = Core(sampling_frequency, sequence_length, baud_rate, carrier_frequency, snr, enable_noise)

    n = repeat_count
    data_y = []
    data_x = []
    num = int((to_db - from_db) / step_db + 1)
    cnt = 0
    for snr in np.linspace(from_db, to_db, num):
        cnt += 1
        core.setSnr(snr)
        counter = 0
        for i in range(n):
            counter += core.process()
        data_x.append(snr)
        y = counter / n
        data_y.append(y)
        dpg.set_value('progress_bar', cnt / num)
        dpg.set_value('research', [np.array(data_x), np.array(data_y)])
        dpg.fit_axis_data('research_x_axis')
        dpg.fit_axis_data('research_y_axis')


def research_start():
    print("Researching...")
    dpg.disable_item('research_btn')
    dpg.set_axis_limits('research_x_axis', dpg.get_value("from_db"), dpg.get_value("to_db"))
    dpg.set_value('tab_bar', 'research_tab')
    from_db = dpg.get_value('from_db')
    to_db = dpg.get_value('to_db')
    step_db = dpg.get_value('step_db')
    repeat_count = dpg.get_value('repeat_count')
    research(from_db, to_db, step_db, repeat_count)
    dpg.enable_item('research_btn')


def process():
    sampling_frequency = dpg.get_value("sampling_frequency")
    sequence_length = dpg.get_value("sequence_length")
    baud_rate = dpg.get_value("baud_rate")
    carrier_frequency = dpg.get_value("carrier_frequency")
    snr = dpg.get_value("snr")
    enable_noise = dpg.get_value("enable_noise")

    core = Core(sampling_frequency, sequence_length, baud_rate, carrier_frequency, snr, enable_noise)
    core.process()

    dpg.set_value('signal_series0', [core.correlate_xis, core.correlate_yis[0]])
    dpg.set_value('signal_series1', [core.correlate_xis, core.correlate_yis[1]])
    dpg.set_value('signal_series2', [core.correlate_xis, core.correlate_yis[2]])
    dpg.set_value('signal_series3', [core.correlate_xis, core.correlate_yis[3]])
    dpg.fit_axis_data('signal_x_axis')
    dpg.fit_axis_data('signal_y_axis')


# Window
dpg.create_context()
with dpg.window() as main_window:
    with dpg.group(horizontal=True):
        with dpg.child_window(width=300) as setting_child_window:
            with dpg.collapsing_header(label="Main parameters", default_open=True):
                dpg.add_text('Sampling Frequency [kHz]:')
                dpg.add_input_float(width=-1, default_value=6, tag='sampling_frequency')
                dpg.add_spacer()
                dpg.add_text('Sequence Length [bits]:')
                dpg.add_input_int(width=-1, default_value=16, tag='sequence_length')
                dpg.add_spacer()
                dpg.add_text('Baud Rate [bits/sec]:')
                dpg.add_input_int(width=-1, default_value=100, tag='baud_rate')
                dpg.add_spacer()
                dpg.add_text('Carrier Frequency [kHz]:')
                dpg.add_input_float(width=-1, default_value=0.1, tag='carrier_frequency')
                dpg.add_spacer()
                dpg.add_text('SNR [dB]:')
                dpg.add_input_int(width=-1, default_value=10, tag='snr')
                dpg.add_checkbox(label="Enable Noise", tag="enable_noise", default_value=True)
                dpg.add_spacer()

            with dpg.collapsing_header(label="Research parameters"):
                dpg.add_text('From [dB]:')
                dpg.add_input_float(width=-1, default_value=-30, tag='from_db')
                dpg.add_spacer()
                dpg.add_text('To [dB]:')
                dpg.add_input_float(width=-1, default_value=10, tag='to_db')
                dpg.add_spacer()
                dpg.add_text('Step [dB]:')
                dpg.add_input_float(width=-1, default_value=1, tag='step_db')
                dpg.add_spacer()
                dpg.add_text('Repeat Count [number]:')
                dpg.add_input_int(width=-1, default_value=100, tag='repeat_count')
                dpg.add_spacer()

            dpg.add_button(label="Generate Signal", width=-1, callback=process)
            dpg.add_button(label="Start Research", width=-1, callback=research_start, tag='research_btn')
            dpg.add_progress_bar(label="Progress Bar", width=-1, tag='progress_bar')

        with dpg.tab_bar(tag='tab_bar'):
            with dpg.tab(label="Main", tag="main_tab"):
                with dpg.child_window(tag="plot_window", border=False) as plot_child_window:
                    with dpg.subplots(rows=1, columns=1, no_title=True, width=-1, height=-1):
                        with dpg.plot(label="Signal", anti_aliased=True, tag='graph'):
                            dpg.add_plot_legend()
                            dpg.add_plot_axis(dpg.mvXAxis, label="time [ms]", tag="signal_x_axis")
                            dpg.add_plot_axis(dpg.mvYAxis, label="y", tag="signal_y_axis")
                            dpg.add_line_series([], [], parent="signal_y_axis", tag="signal_series")
                            dpg.add_line_series([], [], parent="signal_y_axis", tag="signal_series0")
                            dpg.add_line_series([], [], parent="signal_y_axis", tag="signal_series1")
                            dpg.add_line_series([], [], parent="signal_y_axis", tag="signal_series2")
                            dpg.add_line_series([], [], parent="signal_y_axis", tag="signal_series3")
            with dpg.tab(label="Research", tag="research_tab"):
                with dpg.child_window(tag="research_window", border=False):
                    with dpg.subplots(rows=1, columns=1, no_title=True, width=-1, height=-1):
                        with dpg.plot(label="Error", anti_aliased=True):
                            dpg.add_plot_legend()
                            dpg.add_plot_axis(dpg.mvXAxis, label="SNR [dB]", tag="research_x_axis")
                            dpg.add_plot_axis(dpg.mvYAxis, label="Bit Error Rate", tag="research_y_axis", log_scale=True)
                            dpg.set_axis_limits('research_y_axis', -0.1, 1.1)
                            dpg.add_line_series([], [], parent="research_y_axis", tag='research', label='QPSK')

dpg.create_viewport(title="Signal Delay Estimation", width=1920, height=1080)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window(main_window, True)
dpg.start_dearpygui()
dpg.destroy_context()
