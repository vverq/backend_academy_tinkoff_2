import os


def main():
    metric = ["# HELP log_size_bytes Size of log files in bytes", "# TYPE log_size_bytes counter"]
    log_directory = "/home/oncall/var/log/uwsgi"
    for filename in [file for file in os.listdir(log_directory) if os.path.isfile(os.path.join(log_directory, file))]:
        file_size = os.path.getsize(os.path.join(log_directory, filename))
        metric_value = "log_size_bytes{file=\"" + filename + "\"}" + f" {file_size}"
        metric.append(metric_value)
    print(*metric, file=open('/var/lib/node_exporter/textfile_collector/log_size.prom', "w"), sep="\n", end="\n")


if __name__ == '__main__':
    main()
