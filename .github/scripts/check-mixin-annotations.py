#!/usr/bin/env python3
"""Fails when a jar's mixin config lists a class that has no @Mixin annotation.

Mixin refuses to start the game on such a class, even when the config plugin would never apply it. The version
preprocessor makes this easy to reintroduce: an #else branch that leaves an empty, unannotated class behind.
"""
import json
import sys
import zipfile

MIXIN_DESCRIPTOR = b"Lorg/spongepowered/asm/mixin/Mixin;"


def unannotated(jar_path):
    with zipfile.ZipFile(jar_path) as jar:
        names = set(jar.namelist())
        for config_name in sorted(n for n in names if "/" not in n and n.endswith(".mixins.json")):
            config = json.loads(jar.read(config_name))
            package = config["package"].replace(".", "/")
            for side in ("mixins", "client", "server"):
                for mixin in config.get(side, []):
                    class_name = f"{package}/{mixin.replace('.', '/')}.class"
                    if class_name not in names:
                        yield config_name, class_name, "is missing from the jar"
                    elif MIXIN_DESCRIPTOR not in jar.read(class_name):
                        yield config_name, class_name, "has no @Mixin annotation"


failures = 0
for path in sys.argv[1:]:
    for config_name, class_name, problem in unannotated(path):
        print(f"::error::{path}: {class_name} is listed in {config_name} but {problem}")
        failures += 1
print(f"checked {len(sys.argv) - 1} jar(s), {failures} problem(s)")
sys.exit(1 if failures else 0)