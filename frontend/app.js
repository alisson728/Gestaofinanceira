
let chart;

function abrirModal(){
 document.getElementById('modal').classList.remove('hidden');
}

window.onclick = (e)=>{
 if(e.target.id==='modal'){
  modal.classList.add('hidden');
 }
}

async function salvar(){

 await fetch('/api/lancamentos',{
  method:'POST',
  headers:{'Content-Type':'application/json'},
  body:JSON.stringify({
   tipo:tipo.value,
   descricao:descricao.value,
   valor:valor.value,
   vencimento:vencimento.value
  })
 })

 modal.classList.add('hidden');

 carregar();
}

async function marcarPago(id){

 await fetch('/api/pago/'+id,{
  method:'PATCH'
 })

 carregar();
}

async function excluir(id){

 await fetch('/api/delete/'+id,{
  method:'DELETE'
 })

 carregar();
}

async function carregar(){

 const mes = document.getElementById('mesFiltro').value;

 const dados = await fetch('/api/lancamentos?mes='+mes)
 .then(r=>r.json());

 tbody.innerHTML='';

 let receber = 0;
 let pagar = 0;
 let pendentes = 0;

 dados.forEach(x=>{

  if(x.tipo === 'receber'){
   receber += Number(x.valor);
  }

  if(x.tipo === 'pagar'){
   pagar += Number(x.valor);
  }

  if(x.status !== 'pago'){
   pendentes++;
  }

  tbody.innerHTML += `
  <tr>
   <td>${x.tipo}</td>
   <td>${x.descricao}</td>
   <td>R$ ${Number(x.valor).toFixed(2)}</td>
   <td>${x.vencimento || '-'}</td>
   <td>
    <span class="status ${x.status}">
      ${x.status}
    </span>
   </td>

   <td>
    <div class="acoes">

      ${x.status !== 'pago'
      ? `<button class="btn-pago" onclick="marcarPago(${x.id})">Pago</button>`
      : ''}

      <button class="btn-delete" onclick="excluir(${x.id})">
        Excluir
      </button>

    </div>
   </td>
  </tr>
  `
 })

 const saldo = receber - pagar;

 document.getElementById('receber').innerText = 'R$ '+receber.toFixed(2);
 document.getElementById('pagar').innerText = 'R$ '+pagar.toFixed(2);
 document.getElementById('saldo').innerText = 'R$ '+saldo.toFixed(2);
 document.getElementById('pendentes').innerText = pendentes;

 render(receber,pagar,saldo);
}

function render(receber,pagar,saldo){

 const ctx = document.getElementById('grafico');

 if(chart){
  chart.destroy();
 }

 chart = new Chart(ctx,{
  type:'bar',
  data:{
   labels:['Receber','Pagar','Saldo'],
   datasets:[{
    data:[receber,pagar,saldo],
    backgroundColor:[
      '#00b050',
      '#ef4444',
      '#0ea5e9'
    ],
    borderRadius:14
   }]
  },
  options:{
   responsive:true,
   maintainAspectRatio:false,
   plugins:{
    legend:{
      display:false
    }
   },
   scales:{
    x:{
      grid:{
        display:false
      }
    },
    y:{
      grid:{
        display:false
      }
    }
   }
  }
 })
}

document.getElementById('mesFiltro').addEventListener('change', carregar);

carregar();
