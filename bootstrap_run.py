from streamlit import bootstrap

real_script = 'app.py'

bootstrap.run(real_script, f'run.py {real_script}', [], {})