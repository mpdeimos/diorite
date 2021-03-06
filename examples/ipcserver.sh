#!/bin/bash

# Author: Jiří Janoušek <janousek.jiri@gmail.com>
#
# To the extent possible under law, author has waived all
# copyright and related or neighboring rights to this file.
# http://creativecommons.org/publicdomain/zero/1.0/
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHORS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

if [ "$#" -lt 2 ]; then
	echo "Usage: $0 build|dist|run lin|mingw"
	exit 1
fi

set -eu
NAME="ipcserver"
CMD="$1"
PLATFORM="$2"
. conf.inc.sh 

build()
{
	dist
	echo "*** $0 build ***"
	mkdir -p ${OUT}
	valac -d ${OUT} -b . --thread --save-temps -v \
	-o ${NAME}${EXECSUFFIX} \
	--vapidir $BUILD -X -I$BUILD -X -L$BUILD \
	--vapidir ../vapi --pkg glib-2.0 --target-glib=2.32 \
	--pkg=dioriteglib \
	-X '-DG_LOG_DOMAIN="MyDiorite"' \
	${NAME}.vala
}



run()
{
	build
	dist
	echo "*** $0 run ***"
	set -x
	${LAUNCHER} ${OUT}/${NAME}${EXECSUFFIX}
}

$CMD
