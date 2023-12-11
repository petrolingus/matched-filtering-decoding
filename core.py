import numpy as np
import scipy as sci
from pylfsr import LFSR


def applyNoise(signal, snr):
    # Calculate the power of the signal
    signal_power = np.square(signal).mean()
    # Calculate the noise power based on the desired SNR and signal power
    noise_power = signal_power / (10 ** (snr / 10))
    # Generate the noise with the calculated power
    noise = np.random.normal(0, np.sqrt(noise_power), len(signal))
    return signal + noise


class Core:
    def __init__(self, sampling_frequency, sequence_length, baud_rate, carrier_frequency, snr, enable_noise):
        self.sampling_frequency = sampling_frequency * 1000  # Hz
        self.sequence_length = sequence_length
        self.baud_rate = baud_rate
        self.carrier_frequency = carrier_frequency * 1000  # Hz
        self.snr = snr
        self.enable_noise = enable_noise
        # Calculations
        self.signal_duration = self.sequence_length / self.baud_rate  # seconds
        self.samples_per_bit = int(np.round(self.sampling_frequency / self.baud_rate))
        # Gold Codes
        self.gold_code_length = 0
        self.gold_codes = []
        self.generate_gold_codes()
        # Signals
        self.signal_xis = None
        self.signal_yis = None
        self.gold_signal_xis = None
        self.gold_signal_yis = None
        self.signal_psk = None
        self.gold_psk = None
        self.correlate_xis = None
        self.correlate_yis = None

    def setSnr(self, snr):
        self.snr = snr

    def generate_gold_codes(self):
        # seq1 = LFSR(initstate=[1, 1, 1, 1, 1, 1, 1], fpoly=[7, 3, 2, 1]).runKCycle(64)
        # seq2 = LFSR(initstate=[1, 1, 1, 1, 1, 1, 1], fpoly=[7, 5, 4, 3, 2, 1]).runKCycle(64)
        seq1 = LFSR(initstate=[1, 1, 1, 1, 1], fpoly=[5, 3]).getFullPeriod()
        seq2 = LFSR(initstate=[1, 1, 1, 1, 1], fpoly=[5, 4, 3, 2]).getFullPeriod()
        gold_codes = []
        for i in range(4):
            x = np.bitwise_xor(seq1, np.roll(seq2, -i))
            gold_codes.append(x)
        self.gold_code_length = len(gold_codes[0])
        self.gold_codes = np.array(gold_codes)
        # print('self.gold_codes.size', len(self.gold_codes))
        # print('self.gold_code_length', self.gold_code_length)

    def process(self):

        sequence = np.random.randint(4, size=self.sequence_length // 2)
        transform = np.concatenate([self.gold_codes[i] for i in sequence])
        # print('transform.size', transform.size)

        # Generation Signal
        signal_duration = transform.size / self.baud_rate  # seconds
        samples_per_bit = int(np.round(self.sampling_frequency / self.baud_rate))
        self.signal_xis = np.arange(0, signal_duration, 1 / self.sampling_frequency)
        self.signal_yis = np.repeat(transform, int(samples_per_bit))
        # print('signal_xis.size', self.signal_xis.size)
        # print('signal_yis.size', self.signal_yis.size)

        # Generation Gold Signals
        gold_signal_duration = self.gold_code_length / self.baud_rate  # seconds
        self.gold_signal_xis = np.arange(0, gold_signal_duration, 1 / self.sampling_frequency)
        self.gold_signal_yis = np.repeat(self.gold_codes, samples_per_bit).reshape(4, self.gold_signal_xis.size)
        # print('gold_signal_xis.size', self.gold_signal_xis.size)
        # print('gold_signal_yis.size', self.gold_signal_yis.size // 4)

        # Modulation Signal
        signal_psk_sin = np.sin(
            2 * np.pi * self.carrier_frequency * self.signal_xis + np.pi * np.array(self.signal_yis))
        signal_psk_cos = np.cos(
            2 * np.pi * self.carrier_frequency * self.signal_xis + np.pi * np.array(self.signal_yis))
        self.signal_psk = (signal_psk_sin + signal_psk_cos) / 2.0
        # print('signal_psk.size', self.signal_psk.size)

        # Modulation Sold Signals
        gold_psk_sin = np.sin(2 * np.pi * self.carrier_frequency * self.gold_signal_xis + np.pi * self.gold_signal_yis)
        gold_psk_cos = np.cos(2 * np.pi * self.carrier_frequency * self.gold_signal_xis + np.pi * self.gold_signal_yis)
        self.gold_psk = (gold_psk_sin + gold_psk_cos) / 2.0
        # print('gold_psk.size', self.gold_psk.size // 4)

        # Apply noise
        if self.enable_noise:
            self.signal_psk = applyNoise(self.signal_psk, self.snr)

        # Correlation
        correlate_yis0 = sci.signal.correlate(self.signal_psk, self.gold_psk[0], mode='same', method='fft')
        correlate_yis1 = sci.signal.correlate(self.signal_psk, self.gold_psk[1], mode='same', method='fft')
        correlate_yis2 = sci.signal.correlate(self.signal_psk, self.gold_psk[2], mode='same', method='fft')
        correlate_yis3 = sci.signal.correlate(self.signal_psk, self.gold_psk[3], mode='same', method='fft')
        self.correlate_xis = np.arange(correlate_yis0.size) / self.sampling_frequency
        self.correlate_yis = np.array([correlate_yis0, correlate_yis1, correlate_yis2, correlate_yis3])
        # print('self.correlate_yis.size', self.correlate_yis.size)
        # print('self.correlate_yis.size//4', self.correlate_yis.size // 4)

        # Max Search
        segments = transform.size // self.gold_code_length
        # print('segments', segments)

        resize0 = correlate_yis0.reshape(segments, -1)
        resize1 = correlate_yis1.reshape(segments, -1)
        resize2 = correlate_yis2.reshape(segments, -1)
        resize3 = correlate_yis3.reshape(segments, -1)

        np_max0 = np.max(resize0, axis=1)
        np_max1 = np.max(resize1, axis=1)
        np_max2 = np.max(resize2, axis=1)
        np_max3 = np.max(resize3, axis=1)

        a = np.array([np_max0, np_max1, np_max2, np_max3])

        result_sequence = np.argmax(a, axis=0)

        # print('results:')
        # print('target', sequence)
        # print('search', result_sequence)

        err_count = 0
        for i in np.arange(sequence.size):
            if sequence[i] & 1 != result_sequence[i] & 1:
                err_count += 1
            if sequence[i] & 2 != result_sequence[i] & 2:
                err_count += 1

        ber = err_count / (2 * sequence.size)
        # print('ber', ber)
        return ber
